from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SiteTheme:
    key: str
    display_name: str
    mark: str
    nav: tuple[str, ...]
    hero_title: str
    hero_body: str
    primary_cta: str
    secondary_cta: str
    cards: tuple[tuple[str, str], ...]
    stat_label: str
    stat_value: str
    footer_note: str


_GENERIC = SiteTheme(
    key="generic",
    display_name="Fictional service",
    mark="F",
    nav=("Overview", "Account", "Help"),
    hero_title="A local service workspace",
    hero_body=(
        "This fictional page is part of a controlled training simulation."
    ),
    primary_cta="Continue",
    secondary_cta="Learn more",
    cards=(
        ("Local workspace", "All activity stays on this machine."),
        ("Training context", "No real account or external service is used."),
    ),
    stat_label="Workspace",
    stat_value="Local",
    footer_note="Fictional local service · no external account is contacted",
)

_THEMES: dict[str, SiteTheme] = {
    "gmail": SiteTheme(
        key="gmail",
        display_name="Gemail",
        mark="M",
        nav=("Inbox", "Starred", "Snoozed", "Sent", "Drafts"),
        hero_title="Your mailbox",
        hero_body="A familiar mail workspace for fictional Northstar messages.",
        primary_cta="Open inbox",
        secondary_cta="Compose",
        cards=(
            ("Inbox", "Messages and conversations stay in this local mailbox."),
            ("Labels", "Use the folders to organize the training context."),
        ),
        stat_label="Mailbox",
        stat_value="Personal",
        footer_note="Fictional Gemail · messages are not delivered",
    ),
    "quickchat": SiteTheme(
        key="quickchat",
        display_name="QuickChat",
        mark="Q",
        nav=("Chats", "Calls", "Saved"),
        hero_title="Your conversations",
        hero_body=(
            "A compact messaging space for fictional delivery and support "
            "threads."
        ),
        primary_cta="Open messages",
        secondary_cta="Start a chat",
        cards=(
            (
                "Recent chats",
                "Conversation previews appear in the message list.",
            ),
            (
                "Local only",
                "No phone number or messaging provider is contacted.",
            ),
        ),
        stat_label="Inbox",
        stat_value="Personal",
        footer_note="Fictional QuickChat · no message is sent",
    ),
    "unisecure": SiteTheme(
        key="unisecure",
        display_name="UniSecure",
        mark="U",
        nav=("Overview", "Mailbox", "Security", "Help"),
        hero_title="Northstar account center",
        hero_body=(
            "Review your university identity, mailbox access, and account "
            "security."
        ),
        primary_cta="Verify mailbox access",
        secondary_cta="View account status",
        cards=(
            ("Mailbox access", "Northstar University · student services"),
            ("Security status", "A recent sign-in requires attention"),
            ("Service desk", "Fictional Northstar IT support"),
        ),
        stat_label="Account",
        stat_value="Student",
        footer_note=(
            "Fictional UniSecure · Northstar University training portal"
        ),
    ),
    "support": SiteTheme(
        key="support",
        display_name="UniSecure Support",
        mark="S",
        nav=("Support home", "My tickets", "Knowledge base"),
        hero_title="Northstar IT support desk",
        hero_body=(
            "A support workspace for reviewing account alerts and "
            "verification requests."
        ),
        primary_cta="Open support case",
        secondary_cta="Browse help articles",
        cards=(
            ("Ticket #NS-4821", "Unknown device sign-in detected"),
            (
                "Service status",
                "IT support is available for this fictional case",
            ),
            ("Next step", "Complete the requested account verification"),
        ),
        stat_label="Case",
        stat_value="#NS-4821",
        footer_note="Fictional UniSecure Support · no support case is opened",
    ),
    "amazaun": SiteTheme(
        key="amazaun",
        display_name="Amazaun",
        mark="a",
        nav=("Home", "Orders", "Cart", "Account"),
        hero_title="Your order is ready",
        hero_body=(
            "Review the fictional delivery details before your package is "
            "released."
        ),
        primary_cta="Confirm delivery address",
        secondary_cta="View order details",
        cards=(
            ("Order status", "Awaiting delivery confirmation"),
            ("Delivery", "Local training address · no carrier contacted"),
            ("Account", "Amazaun Marketplace"),
        ),
        stat_label="Order",
        stat_value="Pending",
        footer_note="Fictional Amazaun Marketplace · no order is placed",
    ),
    "cloudbox": SiteTheme(
        key="cloudbox",
        display_name="CloudBox",
        mark="C",
        nav=("Files", "Shared", "Activity", "Trash"),
        hero_title="Your CloudBox workspace",
        hero_body=(
            "Shared files and workspace activity in one focused storage "
            "dashboard."
        ),
        primary_cta="Review shared files",
        secondary_cta="View storage activity",
        cards=(
            ("Shared with you", "Design Lab · brand files"),
            ("Storage", "Workspace capacity is nearly full"),
            ("Activity", "A recent sign-in needs verification"),
        ),
        stat_label="Storage",
        stat_value="92% used",
        footer_note="Fictional CloudBox · files are not uploaded or downloaded",
    ),
    "paymate": SiteTheme(
        key="paymate",
        display_name="PayMate",
        mark="P",
        nav=("Overview", "Payments", "Invoices", "Support"),
        hero_title="Payment review center",
        hero_body=(
            "Review a pending payment request before the local hold expires."
        ),
        primary_cta="Review payment",
        secondary_cta="View payment history",
        cards=(
            ("Pending payment", "Invoice #1042-991"),
            ("Amount", "Fictional local invoice total"),
            ("Review status", "Confirmation is required"),
        ),
        stat_label="Payment",
        stat_value="Pending",
        footer_note="Fictional PayMate Payments · no funds move",
    ),
    "makexam": SiteTheme(
        key="makexam",
        display_name="MAKExam",
        mark="M",
        nav=("Home", "Registration", "Exams", "Results"),
        hero_title="Assessment registration",
        hero_body=(
            "Northstar Institute of Technology examination services in one "
            "place."
        ),
        primary_cta="Continue exam registration",
        secondary_cta="View exam schedule",
        cards=(
            ("Registration window", "Local assessment access"),
            ("Student record", "Northstar Institute of Technology"),
            ("Next step", "Confirm your registration ID"),
        ),
        stat_label="Term",
        stat_value="Autumn",
        footer_note="Fictional MAKExam · no examination is registered",
    ),
    "technosphere": SiteTheme(
        key="technosphere",
        display_name="TechnoSphere",
        mark="T",
        nav=("Course home", "Calendar", "Messages", "Resources"),
        hero_title="Course workspace",
        hero_body=(
            "A faculty workspace for courses, messages, and shared learning "
            "resources."
        ),
        primary_cta="Open course workspace",
        secondary_cta="View course calendar",
        cards=(
            ("Course workspace", "New faculty course activity"),
            ("Calendar", "Upcoming local course sessions"),
            ("Resources", "Shared course materials"),
        ),
        stat_label="Workspace",
        stat_value="Faculty",
        footer_note="Fictional TechnoSphere · no course account is changed",
    ),
    "nimbusid": SiteTheme(
        key="nimbusid",
        display_name="NimbusID",
        mark="N",
        nav=("Security", "Devices", "Activity"),
        hero_title="Sign-in approval",
        hero_body=(
            "Review a fictional sign-in request before it is approved or "
            "denied."
        ),
        primary_cta="Review request",
        secondary_cta="View device activity",
        cards=(
            ("Unknown device", "Fictional Chrome on Linux"),
            ("Location", "Northstar campus network"),
            ("Requested access", "Mailbox and course services"),
        ),
        stat_label="Requests",
        stat_value="1 pending",
        footer_note="Fictional NimbusID · no approval is sent",
    ),
}

_SITE_SCENARIOS = {
    "credential-basic-001": "unisecure",
    "qr-phish-001": "unisecure",
    "credential-shopping-001": "amazaun",
    "credential-cloud-001": "cloudbox",
    "credential-payment-001": "paymate",
    "support-portal-001": "support",
    "mak-exam-001": "makexam",
    "technosphere-001": "technosphere",
}


def get_site_theme(
    scenario_id: str | None = None,
    channel: str | None = None,
) -> SiteTheme:
    if scenario_id in _SITE_SCENARIOS:
        return _THEMES[_SITE_SCENARIOS[scenario_id]]
    if channel == "email":
        return _THEMES["gmail"]
    if channel == "sms":
        return _THEMES["quickchat"]
    if channel == "mfa":
        return _THEMES["nimbusid"]
    return _GENERIC
