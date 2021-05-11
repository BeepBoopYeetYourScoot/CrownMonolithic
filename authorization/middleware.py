from authorization.services.get_player import get_player_from_token
from django.utils.deprecation import MiddlewareMixin


class PlayerAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            token = request.headers['Authorization'].split(' ')[1]
            request.player = get_player_from_token(token)
        except (KeyError, IndexError):
            print('no token')
        except ValueError:
            print('not a player')
