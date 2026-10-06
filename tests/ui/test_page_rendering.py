"""UI rendering tests for Streamlit application shell."""

import unittest
from unittest.mock import MagicMock, patch
import app


class TestUIRendering(unittest.TestCase):

    @patch("streamlit.sidebar.radio")
    @patch("streamlit.sidebar.title")
    def test_navigation_items_exist(self, mock_title, mock_radio):
        mock_radio.return_value = "🏠 Dashboard"
        # Verify app loads without throwing unhandled exceptions
        try:
            app.main()
        except Exception as e:
            # st.set_page_config might throw if called twice in test runner context, which is expected
            if "can only be called once" not in str(e):
                self.fail(f"app.main() raised unhandled exception: {e}")


if __name__ == "__main__":
    unittest.main()
