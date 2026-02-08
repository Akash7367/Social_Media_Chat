
import unittest
import pandas as pd
from preprocessor import preprocess

class TestPreprocessor(unittest.TestCase):
    def test_24h_format(self):
        data = "26/01/23, 15:30 - User1: Hello there\n26/01/23, 15:31 - User2: Hi!\n"
        df = preprocess(data)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['message'].strip(), "Hello there")
        self.assertEqual(df.iloc[0]['user'], "User1")
        self.assertEqual(df.iloc[0]['hour'], 15)

    def test_12h_format(self):
        data = "01/26/23, 03:30 PM - User1: Hello\n01/26/23, 03:31 PM - User2: Hi\n"
        df = preprocess(data)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['hour'], 15) # 3 PM is 15
        self.assertEqual(df.iloc[0]['user'], "User1")

    def test_ios_format(self):
        data = "[26/01/23, 15:30:00] User1: Hello\n[26/01/23, 15:31:00] User2: Hi\n"
        df = preprocess(data)
        self.assertEqual(len(df), 2)
        # Check if ios format correctly extracts user (parsing logic might differ slightly based on user splitting)
        # My logic assumes ": " splits user and message.
        # In "[date] User: Msg", splitting by date regex gives " User1: Hello" in user_message column probably?
        # Let's check regex split behavior.
        # Regex: \[...\]\s
        # Split gives ["", "User1: Hello\n", "User2: Hi\n"]
        # df['user_message'] would be "User1: Hello\n"
        self.assertEqual(df.iloc[0]['user'], "User1")
        self.assertEqual(df.iloc[0]['message'].strip(), "Hello")

if __name__ == '__main__':
    unittest.main()
