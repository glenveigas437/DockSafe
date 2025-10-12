from flask import (
    request,
    jsonify,
    render_template,
    session,
    current_app,
    flash,
    redirect,
    url_for,
)
from app.models import Group, User, VulnerabilityScan, user_groups
from app import db
from app.decorators import login_required
from sqlalchemy import and_, or_
import logging
from datetime import datetime
from app.groups import bp

logger = logging.getLogger(__name__)


@bp.route("/")
@login_required
def index():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return render_template("groups/index.html", groups=[])

        user = User.query.get(user_id)
        if not user:
            return render_template("groups/index.html", groups=[])

        groups_data = []
        for group in user.groups:
            scan_count = VulnerabilityScan.query.filter_by(group_id=group.id).count()

            role_result = db.session.execute(
                db.select(user_groups.c.role).where(
                    and_(
                        user_groups.c.user_id == user_id,
                        user_groups.c.group_id == group.id,
                    )
                )
            ).scalar()

            groups_data.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "member_count": len(list(group.members)),
                    "scan_count": scan_count,
                    "role": role_result or "member",
                    "created_at": group.created_at.isoformat()
                    if group.created_at
                    else None,
                }
            )

        selected_group_id = session.get("selected_group_id")

        return render_template(
            "groups/index.html", groups=groups_data, selected_group_id=selected_group_id
        )

    except Exception as e:
        logger.error(f"Error loading groups: {e}")
        return render_template("groups/index.html", groups=[])


@bp.route("/select", methods=["POST"])
@login_required
def select_group_api():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        data = request.get_json()
        group_id = data.get("group_id")

        if not group_id:
            return jsonify({"error": "Group ID is required"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_groups = [group.id for group in user.groups]
        if group_id not in user_groups:
            return jsonify({"error": "You are not a member of this group"}), 403

        session["selected_group_id"] = group_id

        return jsonify({"success": True, "message": "Group selected successfully"})

    except Exception as e:
        logger.error(f"Error selecting group: {e}")
        return jsonify({"error": "Failed to select group"}), 500


@bp.route("/select")
@login_required
def select_group():
    return redirect(url_for("main.dashboard"))


@bp.route("/list")
@login_required
def list_groups():
    try:
        user_id = session.get("user_id")
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_groups_list = user.groups.filter_by(is_active=True).all()

        groups_data = []
        for group in user_groups_list:
            group_data = group.to_dict()
            group_data["role"] = group.get_user_role(user)
            group_data["scan_count"] = len(list(group.scans))
            groups_data.append(group_data)

        return jsonify({"success": True, "groups": groups_data})

    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        return jsonify({"error": "Failed to list groups"}), 500


@bp.route("/create", methods=["POST"])
@login_required
def create_group():
    try:
        user_id = session.get("user_id")
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()

        if not name:
            return jsonify({"error": "Group name is required"}), 400

        existing_group = Group.find_by_name(name)
        if existing_group:
            return jsonify({"error": "Group name already exists"}), 400

        group = Group(
            name=name, description=description, created_by=user.id, is_active=True
        )

        db.session.add(group)
        db.session.commit()

        group.add_member(user, role="owner")

        return jsonify(
            {
                "success": True,
                "group": group.to_dict(),
                "message": f'Group "{name}" created successfully',
            }
        )

    except Exception as e:
        logger.error(f"Error creating group: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create group"}), 500


@bp.route("/search")
@login_required
def search_groups():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"success": True, "groups": []})

        groups = (
            Group.query.filter(
                and_(Group.is_active == True, Group.name.ilike(f"%{query}%"))
            )
            .limit(10)
            .all()
        )

        result_groups = []
        for group in groups:
            is_member = group.is_member(user_id)

            result_groups.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "member_count": len(list(group.members)),
                    "is_member": is_member,
                    "created_at": group.created_at.isoformat()
                    if group.created_at
                    else None,
                }
            )

        return jsonify({"success": True, "groups": result_groups})

    except Exception as e:
        logger.error(f"Error searching groups: {e}")
        return jsonify({"error": "Failed to search groups"}), 500


@bp.route("/<int:group_id>/join", methods=["POST"])
@login_required
def join_group(group_id):
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        group = Group.query.get(group_id)
        if not group:
            return jsonify({"error": "Group not found"}), 404

        if not group.is_active:
            return jsonify({"error": "Group is not active"}), 400

        if group.is_member(user):
            return jsonify({"error": "You are already a member of this group"}), 400

        group.add_member(user, role="member")

        logger.info(f"User {user.email} joined group '{group.name}'")

        return jsonify(
            {"success": True, "message": f'Successfully joined group "{group.name}"'}
        )

    except Exception as e:
        logger.error(f"Error joining group: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to join group"}), 500


@bp.route("/<int:group_id>/leave", methods=["POST"])
@login_required
def leave_group(group_id):
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        group = Group.query.get(group_id)
        if not group:
            return jsonify({"error": "Group not found"}), 404

        if not group.is_member(user):
            return jsonify({"error": "You are not a member of this group"}), 400

        user_role = group.get_user_role(user)
        if user_role == "owner":
            return (
                jsonify(
                    {
                        "error": "Group owners cannot leave the group. Transfer ownership first."
                    }
                ),
                400,
            )

        group.remove_member(user)

        logger.info(f"User {user.email} left group '{group.name}'")

        return jsonify(
            {"success": True, "message": f'Successfully left group "{group.name}"'}
        )

    except Exception as e:
        logger.error(f"Error leaving group: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to leave group"}), 500


@bp.route("/<int:group_id>/manage")
@login_required
def manage_group(group_id):
    try:
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("auth.login"))

        user = User.query.get(user_id)
        if not user:
            return redirect(url_for("auth.login"))

        group = None
        user_role = None
        for g in user.groups:
            if g.id == group_id:
                group = g
                role_result = db.session.execute(
                    db.select(user_groups.c.role).where(
                        and_(
                            user_groups.c.user_id == user_id,
                            user_groups.c.group_id == group_id,
                        )
                    )
                ).scalar()
                user_role = role_result or "member"
                break

        if not group:
            flash("You are not a member of this group", "error")
            return redirect(url_for("groups.index"))

        if user_role not in ["admin", "owner"]:
            flash("You do not have permission to manage this group", "error")
            return redirect(url_for("groups.index"))

        members_data = []
        for member in group.members:
            role_result = db.session.execute(
                db.select(user_groups.c.role).where(
                    and_(
                        user_groups.c.user_id == member.id,
                        user_groups.c.group_id == group_id,
                    )
                )
            ).scalar()
            member_role = role_result or "member"

            members_data.append(
                {
                    "id": member.id,
                    "email": member.email,
                    "name": f"{member.first_name} {member.last_name}".strip()
                    if member.first_name or member.last_name
                    else member.email,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "role": member_role,
                    "joined_at": db.session.execute(
                        db.select(user_groups.c.joined_at).where(
                            and_(
                                user_groups.c.user_id == member.id,
                                user_groups.c.group_id == group_id,
                            )
                        )
                    ).scalar(),
                }
            )

        return render_template(
            "groups/manage.html", group=group, members=members_data, user_role=user_role
        )

    except Exception as e:
        logger.error(f"Error loading group management: {e}")
        flash("Error loading group management", "error")
        return redirect(url_for("groups.index"))


@bp.route("/<int:group_id>/members/<int:member_id>/role", methods=["POST"])
@login_required
def update_member_role(group_id, member_id):
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_role_result = db.session.execute(
            db.select(user_groups.c.role).where(
                and_(
                    user_groups.c.user_id == user_id, user_groups.c.group_id == group_id
                )
            )
        ).scalar()
        user_role = user_role_result or "member"

        if user_role not in ["admin", "owner"]:
            return (
                jsonify({"error": "You do not have permission to manage this group"}),
                403,
            )

        data = request.get_json()
        new_role = data.get("role")

        if new_role not in ["member", "admin"]:
            return jsonify({"error": "Invalid role"}), 400

        if new_role == "admin" and user_role != "owner":
            return (
                jsonify({"error": "Only group owners can promote members to admin"}),
                403,
            )

        db.session.execute(
            user_groups.update()
            .where(
                and_(
                    user_groups.c.user_id == member_id,
                    user_groups.c.group_id == group_id,
                )
            )
            .values(role=new_role)
        )
        db.session.commit()

        return jsonify(
            {"success": True, "message": f"Member role updated to {new_role}"}
        )

    except Exception as e:
        logger.error(f"Error updating member role: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update member role"}), 500


@bp.route("/<int:group_id>/members/<int:member_id>/remove", methods=["POST"])
@login_required
def remove_member(group_id, member_id):
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_role_result = db.session.execute(
            db.select(user_groups.c.role).where(
                and_(
                    user_groups.c.user_id == user_id, user_groups.c.group_id == group_id
                )
            )
        ).scalar()
        user_role = user_role_result or "member"

        if user_role not in ["admin", "owner"]:
            return (
                jsonify({"error": "You do not have permission to manage this group"}),
                403,
            )

        member_role_result = db.session.execute(
            db.select(user_groups.c.role).where(
                and_(
                    user_groups.c.user_id == member_id,
                    user_groups.c.group_id == group_id,
                )
            )
        ).scalar()
        member_role = member_role_result or "member"

        if member_role == "owner":
            return jsonify({"error": "Cannot remove the group owner"}), 400

        db.session.execute(
            user_groups.delete().where(
                and_(
                    user_groups.c.user_id == member_id,
                    user_groups.c.group_id == group_id,
                )
            )
        )
        db.session.commit()

        return jsonify({"success": True, "message": "Member removed from group"})

    except Exception as e:
        logger.error(f"Error removing member: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to remove member"}), 500


@bp.route("/<int:group_id>/invite", methods=["POST"])
@login_required
def invite_member(group_id):
    try:
        logger.info(f"Invite member request for group_id: {group_id}")

        user_id = session.get("user_id")
        if not user_id:
            logger.error("No user_id in session")
            return jsonify({"error": "User not authenticated"}), 401

        user = User.query.get(user_id)
        if not user:
            logger.error(f"User not found for user_id: {user_id}")
            return jsonify({"error": "User not found"}), 404

        group = Group.query.get(group_id)
        if not group:
            logger.error(f"Group not found for group_id: {group_id}")
            return jsonify({"error": "Group not found"}), 404

        logger.info(f"User {user.email} attempting to invite to group {group.name}")

        user_role_result = db.session.execute(
            db.select(user_groups.c.role).where(
                and_(
                    user_groups.c.user_id == user_id, user_groups.c.group_id == group_id
                )
            )
        ).scalar()
        user_role = user_role_result or "member"

        if user_role not in ["admin", "owner"]:
            return (
                jsonify({"error": "You do not have permission to manage this group"}),
                403,
            )

        data = request.get_json()
        email = data.get("email")
        role = data.get("role", "member")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        if role not in ["member", "admin"]:
            return jsonify({"error": "Invalid role. Must be member or admin"}), 400

        if role == "admin" and user_role != "owner":
            return (
                jsonify({"error": "Only group owners can promote members to admin"}),
                403,
            )

        invitee = User.query.filter_by(email=email).first()
        if not invitee:
            return jsonify({"error": "User with this email does not exist"}), 404

        existing_membership = db.session.execute(
            db.select(user_groups.c.user_id).where(
                and_(
                    user_groups.c.user_id == invitee.id,
                    user_groups.c.group_id == group_id,
                )
            )
        ).scalar()

        if existing_membership:
            return jsonify({"error": "User is already a member of this group"}), 400

        db.session.execute(
            user_groups.insert().values(
                user_id=invitee.id,
                group_id=group_id,
                role=role,
                joined_at=datetime.utcnow(),
            )
        )
        db.session.commit()

        return jsonify({"success": True, "message": "User Added"})

    except Exception as e:
        logger.error(f"Error inviting member: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to invite member"}), 500
