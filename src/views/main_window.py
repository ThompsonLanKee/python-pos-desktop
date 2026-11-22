
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QSizePolicy,
)


class MainWindow(QMainWindow):
    """
    Main application window.

    Features:
        - Dynamic RBAC navigation
        - Permission-based dashboard widgets
        - Protected page navigation
        - Green application theme
        - Session logout integration
    """

    logout_requested = Signal()

    # --------------------------------------------------
    # PAGE CONFIGURATION
    # --------------------------------------------------

    PAGE_CONFIG = [
        ("▦", "Dashboard", "DASHBOARD_VIEW", "dashboard"),
        ("▣", "Point of Sale", "SALE_CREATE", "sales"),
        ("□", "Products", "PRODUCT_VIEW", "products"),
        ("▤", "Inventory", "INVENTORY_VIEW", "inventory"),
        ("♙", "Customers", "CUSTOMER_VIEW", "customers"),
        ("▥", "Reports", "REPORT_VIEW", "reports"),
        ("♟", "User Management", "USER_VIEW", "users"),
        ("⚙", "Role Management", "ROLE_MANAGE", "roles"),
    ]

    PAGE_PERMISSIONS = {
        page_key: permission
        for icon, label, permission, page_key in PAGE_CONFIG
    }

    PAGE_TITLES = {
        page_key: label
        for icon, label, permission, page_key in PAGE_CONFIG
    }

    PAGE_DESCRIPTIONS = {
        "dashboard": "Welcome to your POS management system.",
        "sales": "Create and process customer sales.",
        "products": "Manage your products and product categories.",
        "inventory": "Monitor and manage inventory.",
        "customers": "Manage customer information.",
        "reports": "View business reports and performance.",
        "users": "Manage application users.",
        "roles": "Manage roles and permissions.",
    }

    # --------------------------------------------------
    # DASHBOARD CONFIGURATION
    # --------------------------------------------------

    DASHBOARD_CARDS = [
        {
            "title": "Today's Sales",
            "value": "0 MMK",
            "detail": "Total sales today",
            "permission": "SALE_CREATE",
        },
        {
            "title": "Total Orders",
            "value": "0",
            "detail": "Orders processed",
            "permission": "SALE_CREATE",
        },
        {
            "title": "Total Products",
            "value": "0",
            "detail": "Registered products",
            "permission": "PRODUCT_VIEW",
        },
        {
            "title": "Inventory",
            "value": "0",
            "detail": "Inventory records",
            "permission": "INVENTORY_VIEW",
        },
        {
            "title": "Customers",
            "value": "0",
            "detail": "Registered customers",
            "permission": "CUSTOMER_VIEW",
        },
    ]

    # --------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------

    def __init__(
        self,
        session,
        session_manager,
        authorization_service
    ):
        super().__init__()

        self.session = session
        self.session_manager = session_manager
        self.authorization_service = authorization_service

        # Retrieve current user's permissions
        self.permissions = (
            self.authorization_service.get_user_permissions(
                self.session.user_id
            )
        )
        self.current_page = None

        self.page_widgets = {}
        self.navigation_buttons = {}

        self.setWindowTitle("POS Management System")
        self.resize(1280, 800)
        self.setMinimumSize(1050, 650)

        self.setStyleSheet(self._get_stylesheet())

        self._build_ui()
        self._build_navigation()

    # --------------------------------------------------
    # MAIN UI
    # --------------------------------------------------

    def _build_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self._build_sidebar()
        main_layout.addWidget(self.sidebar)

        # Main content container
        content_container = QWidget()

        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(
            28, 22, 28, 22
        )
        content_layout.setSpacing(20)

        # Header
        self.header = self._build_header()
        content_layout.addWidget(self.header)

        # Page stack
        self.page_stack = QStackedWidget()

        self.page_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        content_layout.addWidget(self.page_stack)

        main_layout.addWidget(content_container, 1)

    # --------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------

    def _build_sidebar(self):

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)

        layout = QVBoxLayout(sidebar)

        layout.setContentsMargins(
            16, 24, 16, 20
        )

        layout.setSpacing(12)

        # Application branding
        logo = QLabel("POS SYSTEM")
        logo.setObjectName("logo")

        subtitle = QLabel("Management Platform")
        subtitle.setObjectName("logo_subtitle")

        layout.addWidget(logo)
        layout.addWidget(subtitle)

        layout.addSpacing(25)

        # Menu heading
        menu_label = QLabel("MAIN MENU")
        menu_label.setObjectName("menu_label")

        layout.addWidget(menu_label)

        # Dynamic navigation
        self.navigation_layout = QVBoxLayout()
        self.navigation_layout.setSpacing(6)

        layout.addLayout(self.navigation_layout)

        layout.addStretch()

        # Current user information
        user_label = QLabel(
            f"{self.session.full_name}\n"
            f"@{self.session.username}"
        )

        user_label.setObjectName("sidebar_user")
        user_label.setWordWrap(True)

        layout.addWidget(user_label)

        # Logout
        logout_button = QPushButton("↪   Logout")
        logout_button.setObjectName("logout_button")

        logout_button.clicked.connect(self.logout)

        layout.addWidget(logout_button)

        return sidebar

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    def _build_header(self):

        header = QWidget()

        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # Page heading
        title_container = QVBoxLayout()

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("page_title")

        self.page_subtitle = QLabel(
            "Welcome to your POS management system."
        )

        self.page_subtitle.setObjectName("page_subtitle")

        title_container.addWidget(self.page_title)
        title_container.addWidget(self.page_subtitle)

        layout.addLayout(title_container)
        layout.addStretch()

        # User badge
        self.user_badge = QLabel(
            f"●  {self.session.username}"
        )

        self.user_badge.setObjectName("user_badge")

        layout.addWidget(self.user_badge)

        return header

    # --------------------------------------------------
    # RBAC NAVIGATION
    # --------------------------------------------------

    def _build_navigation(self):
        """
        Build navigation using the current user's permissions.
        """

        for icon, label, permission, page_key in self.PAGE_CONFIG:

            # Hide unauthorized modules
            if permission not in self.permissions:
                continue

            # Navigation button
            button = QPushButton(
                f"  {icon}     {label}"
            )

            button.setObjectName("nav_button")
            button.setCheckable(True)

            button.clicked.connect(
                lambda checked=False, key=page_key:
                    self.show_page(key)
            )

            self.navigation_layout.addWidget(button)

            self.navigation_buttons[page_key] = button

            # Create page
            page = self._create_page(
                page_key,
                label
            )

            self.page_widgets[page_key] = page

            self.page_stack.addWidget(page)

        # Select initial page
        self._select_initial_page()

    # --------------------------------------------------
    # INITIAL PAGE
    # --------------------------------------------------

    def _select_initial_page(self):
        """
        Select dashboard when available.
        Otherwise select the first authorized module.
        """

        if "dashboard" in self.page_widgets:

            self.show_page("dashboard")

        elif self.page_widgets:

            first_page = next(
                iter(self.page_widgets)
            )

            self.show_page(first_page)

        else:

            self.show_access_denied()

    # --------------------------------------------------
    # PAGE FACTORY
    # --------------------------------------------------

    def _create_page(self, page_key, title):
        """
        Create the appropriate page.
        """

        if page_key == "dashboard":
            return self._build_dashboard_page()

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            0, 10, 0, 0
        )

        layout.setSpacing(16)

        heading = QLabel(title)
        heading.setObjectName("section_title")

        description = QLabel(
            self.PAGE_DESCRIPTIONS.get(
                page_key,
                f"Manage {title.lower()}."
            )
        )

        description.setObjectName("page_subtitle")

        layout.addWidget(heading)
        layout.addWidget(description)

        layout.addStretch()

        return page

    # --------------------------------------------------
    # DASHBOARD PAGE
    # --------------------------------------------------

    def _build_dashboard_page(self):
        """
        Create a permission-aware dashboard.
        """

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            0, 10, 0, 0
        )

        layout.setSpacing(20)

        # Dashboard heading
        heading = QLabel("Business Overview")
        heading.setObjectName("section_title")

        layout.addWidget(heading)

        description = QLabel(
            "Here is an overview of your business."
        )

        description.setObjectName("page_subtitle")

        layout.addWidget(description)

        # ----------------------------------------------
        # DASHBOARD STATISTICS
        # ----------------------------------------------

        grid = QGridLayout()
        grid.setSpacing(16)

        authorized_cards = [
            card
            for card in self.DASHBOARD_CARDS
            if card["permission"] in self.permissions
        ]

        for index, card_data in enumerate(authorized_cards):

            card = QFrame()
            card.setObjectName("stat_card")

            card_layout = QVBoxLayout(card)

            card_layout.setContentsMargins(
                20, 18, 20, 18
            )

            card_layout.setSpacing(8)

            card_title = QLabel(card_data["title"])
            card_title.setObjectName("card_title")

            card_value = QLabel(card_data["value"])
            card_value.setObjectName("card_value")

            card_detail = QLabel(card_data["detail"])
            card_detail.setObjectName("card_detail")

            card_layout.addWidget(card_title)
            card_layout.addWidget(card_value)
            card_layout.addWidget(card_detail)

            grid.addWidget(
                card,
                index // 2,
                index % 2
            )

        if authorized_cards:

            layout.addLayout(grid)

        else:

            no_widgets = QLabel(
                "No dashboard widgets are available "
                "for your permissions."
            )

            no_widgets.setObjectName("page_subtitle")

            layout.addWidget(no_widgets)

        # ----------------------------------------------
        # RECENT TRANSACTIONS
        # ----------------------------------------------

        can_view_transactions = (
            "SALE_CREATE" in self.permissions
            or "REPORT_VIEW" in self.permissions
        )

        if can_view_transactions:

            transactions = QFrame()
            transactions.setObjectName("stat_card")

            transaction_layout = QVBoxLayout(transactions)

            transaction_layout.setContentsMargins(
                20, 18, 20, 18
            )

            transaction_layout.setSpacing(12)

            transaction_title = QLabel(
                "Recent Transactions"
            )

            transaction_title.setObjectName("section_title")

            transaction_message = QLabel(
                "Transaction records will appear here."
            )

            transaction_message.setObjectName("page_subtitle")

            transaction_layout.addWidget(transaction_title)
            transaction_layout.addWidget(transaction_message)

            layout.addWidget(transactions)

        layout.addStretch()

        return page

    # --------------------------------------------------
    # PAGE NAVIGATION
    # --------------------------------------------------

    def show_page(self, page_key):
        """
        Display a page only if the current user
        has the corresponding permission.
        """

        required_permission = self.PAGE_PERMISSIONS.get(
            page_key
        )

        # Reject unknown pages
        if required_permission is None:
            return

        # Verify cached authorization
        if required_permission not in self.permissions:
            return

        # Verify page availability
        if page_key not in self.page_widgets:
            return

        self.current_page = page_key

        # Change current page
        page = self.page_widgets[page_key]

        self.page_stack.setCurrentWidget(page)

        # Update navigation selection
        for key, button in self.navigation_buttons.items():

            button.setChecked(
                key == page_key
            )

        # Update header
        self.page_title.setText(
            self.PAGE_TITLES.get(
                page_key,
                page_key.title()
            )
        )

        self.page_subtitle.setText(
            self.PAGE_DESCRIPTIONS.get(
                page_key,
                ""
            )
        )

    # --------------------------------------------------
    # ACCESS DENIED
    # --------------------------------------------------

    def show_access_denied(self):
        """
        Display when the user has no accessible modules.
        """

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.addStretch()

        message = QLabel(
            "You do not have permission "
            "to access any module."
        )

        message.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        message.setObjectName("section_title")

        layout.addWidget(message)

        layout.addStretch()

        self.page_stack.addWidget(page)
        self.page_stack.setCurrentWidget(page)

        self.current_page = None

        self.page_title.setText("Dashboard")

        self.page_subtitle.setText(
            "Welcome to your POS management system."
        )

    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------

    def logout(self):
        """
        Terminate the current session and close the window.
        """

        self.session_manager.end()

        self.logout_requested.emit()

        self.close()

    # --------------------------------------------------
    # GREEN THEME
    # --------------------------------------------------

    def _get_stylesheet(self):

        return """

        /* ------------------------------------------
           MAIN WINDOW
        ------------------------------------------ */

        QMainWindow {
            background-color: #F5F7F5;
        }

        QWidget {
            font-family: "Segoe UI";
            color: #26352C;
            font-size: 13px;
        }

        /* ------------------------------------------
           SIDEBAR
        ------------------------------------------ */

        #sidebar {
            background-color: #203D2E;
        }

        #logo {
            color: white;
            font-size: 23px;
            font-weight: bold;
        }

        #logo_subtitle {
            color: #B8CDBE;
            font-size: 11px;
        }

        #menu_label {
            color: #91AA99;
            font-size: 10px;
            font-weight: bold;
        }

        /* ------------------------------------------
           NAVIGATION
        ------------------------------------------ */

        #nav_button {
            background-color: transparent;
            color: #DCE9DF;
            text-align: left;
            padding: 12px 10px;
            border: none;
            border-radius: 7px;
            font-size: 13px;
        }

        #nav_button:hover {
            background-color: #315440;
        }

        #nav_button:checked {
            background-color: #3F7653;
            color: white;
            font-weight: bold;
        }

        /* ------------------------------------------
           USER INFORMATION
        ------------------------------------------ */

        #sidebar_user {
            color: white;
            background-color: #294A37;
            padding: 12px;
            border-radius: 7px;
            font-weight: bold;
        }

        #user_badge {
            background-color: #E4EEE7;
            color: #315D40;
            padding: 10px 15px;
            border-radius: 15px;
            font-weight: bold;
        }

        /* ------------------------------------------
           LOGOUT
        ------------------------------------------ */

        #logout_button {
            background-color: #294A37;
            color: white;
            padding: 11px;
            border: none;
            border-radius: 7px;
        }

        #logout_button:hover {
            background-color: #A94442;
        }

        /* ------------------------------------------
           PAGE HEADER
        ------------------------------------------ */

        #page_title {
            font-size: 25px;
            font-weight: bold;
            color: #203D2E;
        }

        #page_subtitle {
            color: #829087;
            font-size: 12px;
        }

        #section_title {
            font-size: 19px;
            font-weight: bold;
            color: #203D2E;
        }

        /* ------------------------------------------
           DASHBOARD CARDS
        ------------------------------------------ */

        #stat_card {
            background-color: white;
            border: 1px solid #E5EAE6;
            border-radius: 10px;
        }

        #card_title {
            color: #718077;
            font-size: 12px;
        }

        #card_value {
            color: #203D2E;
            font-size: 24px;
            font-weight: bold;
        }

        #card_detail {
            color: #9AA69D;
            font-size: 11px;
        }

        """
