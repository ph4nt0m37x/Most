import networkx as nx
import os
import sys
import django

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'most.settings')
django.setup()

from mostApp.models import Profile, Collaboration


def friends(graph, user):
    return set(graph.neighbors(user))


def friends_of_friends(graph, user):
    user_friends = friends(graph, user)
    user_friends_of_friends = set()

    for friend in user_friends:
        user_friends_of_friends.update(friends(graph, friend) - user_friends)

    return user_friends_of_friends - {user}


def common_friends(graph, user1, user2):
    return friends(graph, user1).intersection(friends(graph, user2))


def number_map_to_sorted_list(friend_map):
    return [v[0] for v in sorted(friend_map.items(), key=lambda kv: (-kv[1], kv[0]))]


def influence_map(graph, user):
    user_friends_of_friends = friends_of_friends(graph, user)
    friend_influence_map = {}

    for friend in user_friends_of_friends:
        user_common_friends = common_friends(graph, user, friend)
        if len(user_common_friends) >= 1:
            friend_influence_map[friend] = sum(
                [1 / len(friends(graph, val)) for val in user_common_friends]
            )

    return friend_influence_map


def recommend_by_influence(graph, user):
    return number_map_to_sorted_list(influence_map(graph, user))


if __name__ == '__main__':
    graph = nx.Graph()
    graph.add_nodes_from(list(Profile.objects.all().values_list('id', flat=True)))
    graph.add_edges_from(list(Collaboration.objects.all().values_list('collaborator_1', 'collaborator_2')))
    print(recommend_by_influence(graph, 1))
    print(recommend_by_influence(graph, 2))
