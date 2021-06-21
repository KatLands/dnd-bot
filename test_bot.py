import unittest
from bot import *

USERNAME = "JaneDoe"
CHANNELNAME = "Testing"
CHANNELID = 1234567890

class MockUser:
    def __init__(self, name: str):
        self.name = name


class MockChannel:
    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id

    @staticmethod
    def send(message: str):
        print(message)


class MockMessage:
    def __init__(self):
        self.author = MockUser(name=USERNAME)
        self.channel = MockChannel(name=CHANNELNAME, id=CHANNELID)


class MockContext:
    def __init__(self):
        self.message = MockMessage()


class TestHelpers(unittest.TestCase):
    def test_is_on_rsvp_accept_list(self):
        trackers["rsvp_accept_session_list"] = [USERNAME]
        self.assertTrue(is_on_rsvp_accept_list(USERNAME))
        trackers["rsvp_accept_session_list"] = []


    def test_is_on_rsvp_decline_list(self):
        trackers["rsvp_decline_session_list"] = [USERNAME]
        self.assertTrue(is_on_rsvp_decline_list(USERNAME))
        trackers["rsvp_decline_session_list"] = []


    def test_check_and_remove_from_rsvp_accept(self):
        trackers["rsvp_accept_session_list"] = [USERNAME]
        check_and_remove_from_rsvp_accept(MockMessage())
        self.assertEqual(len(trackers["rsvp_accept_session_list"]), 0)
        trackers["rsvp_accept_session_list"] = []


    def test_check_and_remove_from_rsvp_decline(self):
        trackers["rsvp_decline_session_list"] = [USERNAME]
        check_and_remove_from_rsvp_decline(MockMessage())
        self.assertEqual(len(trackers["rsvp_decline_session_list"]), 0)
        trackers["rsvp_decline_session_list"] = []


class TestCommands(unittest.TestCase):
    async def test_accept_with_empty_list(self):
        trackers["rsvp_accept_session_list"] = []
        await _accept(MockContext())
        self.assertTrue(USERNAME in trackers["rsvp_accept_session_list"])
        trackers["rsvp_accept_session_list"] = []


    async def test_decline_with_empty_list(self):
        trackers["rsvp_decline_session_list"] = []
        await _decline(MockContext())
        self.assertTrue(USERNAME in trackers["rsvp_decline_session_list"])
        trackers["rsvp_decline_session_list"] = []


    async def test_vote_dream(self):
        trackers["alt_vote_dream_session_list"] = []
        await _dream(MockContext())
        self.assertTrue(USERNAME in trackers["alt_vote_dream_session_list"])
        trackers["alt_vote_dream_session_list"] = []


    async def test_vote_cancel(self):
        trackers["alt_vote_cancel_session_list"] = []
        await _cancel(MockContext())
        self.assertTrue(USERNAME in trackers["alt_vote_cancel_session_list"])
        trackers["alt_vote_cancel_session_list"] = []


if __name__ == '__main__':
    unittest.main()

