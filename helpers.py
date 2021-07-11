# Trackers
class Tracker:
    def __init__(self):
        self.rsvp_accept_session_list = []
        self.rsvp_decline_session_list = []
        self.alt_vote_dream_session_list = []
        self.alt_vote_cancel_session_list = []

    # Helpers
    def is_on_rsvp_accept_list(self, user_name):
        """
        Check if user has signed up to attend
        the session.
        """
        return user_name in self.rsvp_accept_session_list

    def is_on_rsvp_decline_list(self, user_name):
        """
        Check if user has signed up to attend
        the session.
        """
        return user_name in self.rsvp_decline_session_list

    def check_and_remove_from_rsvp_accept(self, message):
        """
        Remove user from RSVP accept.
        """
        user_name = message.author.name
        try:
            self.rsvp_accept_session_list.remove(user_name)
        except ValueError:
            pass

    def check_and_remove_from_rsvp_decline(self, message):
        """
        Remover user from RSVP decline.
        """
        user_name = message.author.name
        try:
            self.rsvp_decline_session_list.remove(user_name)
        except ValueError:
            pass
