from flask import (
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    unset_jwt_cookies,
)
from app.auth import bp
from app.services.user_service import UserService
from app.services.group_service import GroupService
from app.utils.validation_utils import ValidationUtils
from app.constants import ErrorMessages, SessionKeys, HTTPStatusCodes
from app.decorators import login_required
from datetime import datetime
import re

try:
    from app.auth.google_oauth import GoogleOAuthService

    GOOGLE_OAUTH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google OAuth service not available: {e}")
    GOOGLE_OAUTH_AVAILABLE = False
    GoogleOAuthService = None


@bp.route("/login", methods=["GET"])
def login():
    if (
        not GOOGLE_OAUTH_AVAILABLE
        or not GoogleOAuthService
        or not GoogleOAuthService.is_configured()
    ):
        flash(ErrorMessages.GOOGLE_OAUTH_NOT_CONFIGURED, "error")
        return render_template("auth/login.html", error="Google OAuth not configured")

    return render_template("auth/login.html")


@bp.route("/google/login")
def google_login():
    if not GOOGLE_OAUTH_AVAILABLE or not GoogleOAuthService:
        flash(ErrorMessages.GOOGLE_OAUTH_NOT_AVAILABLE, "error")
        return redirect(url_for("auth.login"))

    try:
        oauth_service = GoogleOAuthService()
        authorization_url, state = oauth_service.get_authorization_url()

        # Store state in session with additional debugging
        session[SessionKeys.OAUTH_STATE] = state
        session.permanent = True
        session.modified = True  # Force session to be saved
        current_app.logger.info(f"Generated OAuth state: {state}")
        current_app.logger.info(f"Session ID: {session.get('_id', 'unknown')}")
        current_app.logger.info(f"Session keys: {list(session.keys())}")

        return redirect(authorization_url)
    except Exception as e:
        current_app.logger.error(f"Error initiating Google OAuth: {e}")
        flash("Error initiating Google login. Please try again.", "error")
        return redirect(url_for("auth.login"))


@bp.route("/google/callback")
def google_callback():
    if not GOOGLE_OAUTH_AVAILABLE or not GoogleOAuthService:
        flash(
            "Google OAuth is not available. Please contact your administrator.", "error"
        )
        return redirect(url_for("auth.login"))

    try:
        authorization_code = request.args.get("code")
        state = request.args.get("state")

        current_app.logger.info(
            f"OAuth callback received - Code: {authorization_code[:10] if authorization_code else 'None'}..., State: {state}"
        )
        current_app.logger.info(
            f"Session ID in callback: {session.get('_id', 'unknown')}"
        )
        current_app.logger.info(f"Session keys in callback: {list(session.keys())}")
        current_app.logger.info(f"All session data: {dict(session)}")

        if not authorization_code:
            flash(ErrorMessages.AUTHORIZATION_FAILED, "error")
            return redirect(url_for("auth.login"))

        stored_state = session.get(SessionKeys.OAUTH_STATE)
        if not stored_state:
            current_app.logger.warning("No stored OAuth state found in session")
            flash("OAuth session expired. Please try logging in again.", "error")
            return redirect(url_for("auth.login"))

        if state != stored_state:
            current_app.logger.warning(
                f"State mismatch: stored={stored_state}, received={state}"
            )
            flash("Security validation failed. Please try logging in again.", "error")
            return redirect(url_for("auth.login"))

        session.pop(SessionKeys.OAUTH_STATE, None)

        oauth_service = GoogleOAuthService()

        credentials = oauth_service.exchange_code_for_token(authorization_code)

        user_info = oauth_service.get_user_info(credentials)

        if not user_info.get("verified_email", False):
            flash(ErrorMessages.EMAIL_NOT_VERIFIED, "error")
            return redirect(url_for("auth.login"))

        user = UserService.authenticate_user(user_info)

        if not user.is_active:
            flash(ErrorMessages.ACCOUNT_DEACTIVATED, "error")
            return redirect(url_for("auth.login"))

        access_token = create_access_token(identity=user.id)

        session[SessionKeys.USER_ID] = user.id
        session[SessionKeys.USERNAME] = user.username or user.email.split("@")[0]
        session[SessionKeys.EMAIL] = user.email
        session[SessionKeys.PICTURE_URL] = user.picture_url
        session[SessionKeys.ACCESS_TOKEN] = access_token

        user_groups = UserService.get_user_groups(user.id)

        if len(user_groups) == 0:
            return redirect(url_for("groups.select_group"))

        if len(user_groups) == 1:
            group = user_groups[0]
            session[SessionKeys.SELECTED_GROUP_ID] = group.id
            return redirect(url_for("main.index"))

        return redirect(url_for("main.index", show_group_modal="true"))

    except Exception as e:
        current_app.logger.error(f"Error in Google OAuth callback: {e}")
        flash(ErrorMessages.AUTHENTICATION_FAILED, "error")
        return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET"])
def register():
    return redirect(url_for("auth.login"))


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()

    if request.is_json:
        return jsonify({"message": "Logged out successfully"})

    return redirect(url_for("auth.login"))


@bp.route("/profile")
@login_required
def profile():
    user_id = session.get("user_id")
    user = UserService.get_user_by_id(user_id)

    if not user:
        flash(ErrorMessages.USER_NOT_FOUND, "error")
        return redirect(url_for("auth.login"))

    # Get user's groups
    user_groups = UserService.get_user_groups(user_id)

    return render_template("auth/profile.html", user=user, user_groups=user_groups)


@bp.route("/refresh-profile")
@login_required
def refresh_profile():
    """Force refresh user data from database"""
    user_id = session.get("user_id")
    user = UserService.get_user_by_id(user_id)

    if user:
        # Update session with latest data
        session[SessionKeys.USERNAME] = user.username or user.email.split("@")[0]
        session[SessionKeys.EMAIL] = user.email
        session[SessionKeys.PICTURE_URL] = user.picture_url
        session.modified = True

        flash("Profile data refreshed successfully!", "success")

    return redirect(url_for("auth.profile"))


@bp.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        data = request.get_json()
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"success": False, "message": "User not authenticated"}), 401

        # Update profile
        updated_user = UserService.update_user_profile(
            user_id=user_id,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            country=data.get("country"),
        )

        if not updated_user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Send email verification if requested
        if data.get("send_email_verification", False):
            UserService.send_email_verification(user_id)

        return jsonify({"success": True, "message": "Profile updated successfully"})

    except Exception as e:
        current_app.logger.error(f"Error updating profile: {e}")
        return jsonify({"success": False, "message": "Error updating profile"}), 500


@bp.route("/send-verification", methods=["POST"])
@login_required
def send_verification():
    """Send email verification to user"""
    try:
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"success": False, "message": "User not authenticated"}), 401

        success = UserService.send_email_verification(user_id)

        if success:
            return jsonify(
                {"success": True, "message": "Verification email sent successfully"}
            )
        else:
            return (
                jsonify(
                    {"success": False, "message": "Failed to send verification email"}
                ),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error sending verification email: {e}")
        return (
            jsonify({"success": False, "message": "Error sending verification email"}),
            500,
        )


@bp.route("/verify-email/<token>")
def verify_email(token):
    """Verify user email with token"""
    try:
        success = UserService.verify_email(token)

        if success:
            flash("Email verified successfully! Welcome to DockSafe!", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Invalid or expired verification token.", "error")
            return redirect(url_for("auth.login"))

    except Exception as e:
        current_app.logger.error(f"Error verifying email: {e}")
        flash("Error verifying email. Please try again.", "error")
        return redirect(url_for("auth.login"))
