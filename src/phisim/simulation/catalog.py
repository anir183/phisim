from dataclasses import dataclass

REAL_ORG_DOMAIN = "techno-main.edu"

SIMULATION_REMINDER = (
    "Simulated for security education only. Not an affiliate of any "
    "real institution. No credentials were kept."
)


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    channel: str
    organization: str
    host: str
    title: str
    greeting: str
    message: str
    reminder: str
    indicators: tuple[str, ...]


@dataclass(frozen=True)
class EmailMessage:
    message_id: str
    subject: str
    sender_label: str
    sender_address: str
    body: str
    link_label: str
    host: str
    organization: str
    reminder: str
    indicators: tuple[str, ...]
    spoofed_url: str | None = None
    attachment_name: str | None = None
    attachment_preview: str | None = None


@dataclass(frozen=True)
class SmsThread:
    thread_id: str
    organization: str
    sender_label: str
    sender_number: str
    messages: tuple[str, ...]
    link_label: str
    host: str
    reminder: str
    indicators: tuple[str, ...]
    spoofed_url: str | None = None


@dataclass(frozen=True)
class MfaScenario:
    scenario_id: str
    organization: str
    host: str
    title: str
    service: str
    prompt_count: int
    message: str
    reminder: str
    indicators: tuple[str, ...]


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="credential-basic-001",
        channel="website",
        organization="Techno Main Salt Lake",
        host="techno-main-sl-access.net",
        title="Mailbox Quota Exceeded Notice",
        greeting="Dear student,",
        message=(
            "Your university mailbox quota has been exceeded and will be "
            "suspended within 24 hours unless you confirm your account "
            "details on the login page."
        ),
        reminder=SIMULATION_REMINDER,
        indicators=(
            "credential_request",
            "urgent_language",
            "domain_mismatch",
            "authority_impersonation",
        ),
    ),
    Scenario(
        scenario_id="qr-phish-001",
        channel="qr",
        organization="Techno Main Salt Lake",
        host="techno-main-sl-access.net",
        title="Verification Required",
        greeting="Scan this code to verify your identity.",
        message=(
            "Our security system detected unusual login activity. Scan the "
            "code with your device camera to confirm your account and "
            "restore access."
        ),
        reminder=SIMULATION_REMINDER,
        indicators=(
            "incident_fear",
            "urgent_language",
            "credential_request",
        ),
    ),
)


EMAIL_MESSAGES: tuple[EmailMessage, ...] = (
    EmailMessage(
        message_id="email-phish-001",
        subject="Action required: verify your mailbox",
        sender_label="Techno Main IT Service Desk",
        sender_address=f"helpdesk@{REAL_ORG_DOMAIN}.mail-alert.net",
        body=(
            "We detected a large number of undeliverable messages in your "
            "mailbox. To keep your account active, please verify your "
            "mailbox credentials using the link below.\n\n"
            "Mailboxes that are not verified within 24 hours will be "
            "temporarily suspended."
        ),
        link_label="Verify my mailbox",
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "authority_impersonation",
            "urgent_language",
            "credential_request",
            "domain_mismatch",
        ),
    ),
    EmailMessage(
        message_id="spear-phish-001",
        subject="Re: your scholarship award form",
        sender_label="Dr. Anjali Rao, Dean of Student Affairs",
        sender_address=f"anjali.rao@{REAL_ORG_DOMAIN}",
        body=(
            "I noticed your scholarship award form is still incomplete. The "
            "closing date is tomorrow, so please sign in to the student "
            "portal and finish the last step.\n\n"
            "Let me know once it is done."
        ),
        link_label="Complete my award form",
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "authority_impersonation",
            "personalization",
            "urgent_language",
            "credential_request",
        ),
    ),
    EmailMessage(
        message_id="whaling-001",
        subject="CONFIDENTIAL: vendor payment approval",
        sender_label="Priya Nair, Director of Finance",
        sender_address=f"p.nair@{REAL_ORG_DOMAIN}",
        body=(
            "This payment is now overdue and the vendor is escalating. "
            "Confirm your executive credentials on the finance portal so "
            "the approval can be released before close of business.\n\n"
            "Do not share this with anyone."
        ),
        link_label="Review payment request",
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "authority_impersonation",
            "invoice_fraud",
            "urgent_language",
            "credential_request",
        ),
    ),
    EmailMessage(
        message_id="clone-phish-001",
        subject="Re: file you shared with me",
        sender_label="Kabir Sen",
        sender_address=f"kabir.sen@{REAL_ORG_DOMAIN}",
        body=(
            "I found the shared file, but the link you sent has expired. "
            "Please sign in once more so I can pick up the latest version "
            "from the shared drive.\n\n"
            "Thanks for resending it."
        ),
        link_label="Open shared file",
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "personalization",
            "out_of_band",
            "credential_request",
        ),
    ),
    EmailMessage(
        message_id="urgency-001",
        subject="Your account will be locked at 5:00 PM today",
        sender_label="Account Administration",
        sender_address=f"accounts@{REAL_ORG_DOMAIN}.portals.net",
        body=(
            "A sign-in attempt from an unknown device has triggered a "
            "security review. Confirm your account details before 5:00 PM "
            "today or your access will be suspended indefinitely."
        ),
        link_label="Confirm my account now",
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "urgent_language",
            "incident_fear",
            "credential_request",
            "domain_mismatch",
        ),
    ),
    EmailMessage(
        message_id="tech-support-001",
        subject="Scheduled maintenance requires your password reset",
        sender_label="Techno Main Support",
        sender_address=f"support@{REAL_ORG_DOMAIN}.service-team.net",
        body=(
            "Our maintenance window starts at midnight. To keep your data "
            "safe during the upgrade, every account must rotate its "
            "password today. Use the link below to complete the reset."
        ),
        link_label="Reset my password",
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "tech_support",
            "authority_impersonation",
            "domain_mismatch",
            "credential_request",
        ),
    ),
    EmailMessage(
        message_id="bec-001",
        subject="Invoice #1042-991 outstanding",
        sender_label="Apex Office Supplies",
        sender_address="billing@apex-office-supplies.example",
        body=(
            "Invoice #1042-991 for office supplies remains unpaid. Please "
            "sign in to the invoice portal to review the statement and "
            "initiate the transfer before the account is flagged."
        ),
        link_label="View invoice",
        host="techno-main-sl-access.net",
        organization="Apex Office Supplies",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "invoice_fraud",
            "urgent_language",
            "credential_request",
        ),
    ),
    EmailMessage(
        message_id="link-spoof-001",
        subject="Shared document has been posted",
        sender_label="Collaboration Workspace",
        sender_address=f"no-reply@{REAL_ORG_DOMAIN}.workspace-docs.net",
        body=(
            "A document was shared with you. Open the link below to review "
            "it. You have 24 hours before the link expires."
        ),
        link_label="Open shared document",
        spoofed_url="https://techno-main.edu/documents/shared",
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "spoiled_links",
            "credential_request",
            "domain_mismatch",
        ),
    ),
    EmailMessage(
        message_id="attachment-phish-001",
        subject="Expense reimbursement waiting for you",
        sender_label="HR Operations",
        sender_address=f"hr@{REAL_ORG_DOMAIN}.ops-center.net",
        body=(
            "Your expense reimbursement statement is attached. Review the "
            "summary and sign in to the portal to approve the payout."
        ),
        link_label="Sign in to approve",
        attachment_name="Expense_Reimbursement_Form.pdf",
        attachment_preview=(
            "Simulated PDF preview: a one-page summary titled Expense "
            "Reimbursement. No actual file is attached."
        ),
        host="techno-main-sl-access.net",
        organization="Techno Main Salt Lake",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "attachment_lure",
            "credential_request",
            "domain_mismatch",
        ),
    ),
)


SMS_THREADS: tuple[SmsThread, ...] = (
    SmsThread(
        thread_id="sms-parcel-001",
        organization="Techno Main Parcel",
        sender_label="Techno Main Parcel",
        sender_number="+1 (555) 010-2233",
        messages=(
            "Your package was held at the local delivery center.",
            "Confirm your delivery details to avoid a holding fee.",
            "Reply or confirm now, or the parcel is returned tomorrow.",
        ),
        link_label="Track my package",
        host="techno-main-sl-access.net",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "urgent_language",
            "incident_fear",
            "credential_request",
        ),
    ),
    SmsThread(
        thread_id="sms-tech-support-001",
        organization="Techno Main Salt Lake",
        sender_label="Techno Main Support",
        sender_number="+1 (555) 010-8876",
        messages=(
            "Techno Main Support: unusual sign-in detected on your account.",
            "Tap here to confirm it was you. Your access is limited until "
            "verified.",
            "If you ignore this, your account stays locked.",
        ),
        link_label="Confirm my identity",
        host="techno-main-sl-access.net",
        reminder=SIMULATION_REMINDER,
        indicators=(
            "tech_support",
            "authority_impersonation",
            "credential_request",
        ),
    ),
)


MFA_SCENARIOS: tuple[MfaScenario, ...] = (
    MfaScenario(
        scenario_id="mfa-fatigue-001",
        organization="Techno Main Salt Lake",
        host="login.techno-main-sl-access.net",
        title="Approve Sign-In",
        service="Secure Learning Portal",
        prompt_count=3,
        message=(
            "Every prompt below is a simulated multi-factor approval "
            "request. Approving them all models MFA fatigue, where an "
            "attacker keeps requesting approvals until the user gives in."
        ),
        reminder=SIMULATION_REMINDER,
        indicators=(
            "mfa_fatigue",
            "request_confirmation",
            "urgent_language",
        ),
    ),
)


INDICATOR_INFO: dict[str, str] = {
    "credential_request": "It directly asked for usernames or passwords.",
    "urgent_language": "It applied a deadline or threat to rush your decision.",
    "domain_mismatch": (
        "The real address did not match the organization's known domain."
    ),
    "authority_impersonation": (
        "It pretended to be someone in a position of authority."
    ),
    "personalization": (
        "It used personal or contextual details to appear trustworthy."
    ),
    "spoiled_links": "The visible link text and the real destination differed.",
    "invoice_fraud": (
        "It referenced an invoice or payment that may be fabricated."
    ),
    "attachment_lure": "It used an attachment to persuade a click.",
    "request_confirmation": "It asked you to confirm account or login details.",
    "mfa_fatigue": "It repeatedly asked you to approve a sign-in request.",
    "incident_fear": (
        "It claimed a security incident to demand immediate action."
    ),
    "tech_support": "It impersonated an IT, support, or service team.",
    "out_of_band": (
        "It moved a conversation away from the platform it normally uses."
    ),
}


def get_scenario(scenario_id: str) -> Scenario | None:
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def get_email_message(message_id: str) -> EmailMessage | None:
    for message in EMAIL_MESSAGES:
        if message.message_id == message_id:
            return message
    return None


def get_sms_thread(thread_id: str) -> SmsThread | None:
    for thread in SMS_THREADS:
        if thread.thread_id == thread_id:
            return thread
    return None


def get_mfa_scenario(scenario_id: str) -> MfaScenario | None:
    for scenario in MFA_SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None
