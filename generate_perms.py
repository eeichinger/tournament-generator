#!/usr/bin/env python3

import itertools
import copy
from typing import Callable
from typing import Self

raw_perms = itertools.permutations([1, 2, 3, 4, 5, 6, 7, 8])


def sortperm(perm: tuple) -> tuple:
    assert len(perm) == 8 or len(perm) == 7, "only lists with len=7 or len=8 allowed"
    # print(len(perm))
    # todo: generalise for arbitrary number of elements - atm only len=7 or len=8 handled
    perm_s = sorted(perm[0:2]) + sorted(perm[2:4]) + sorted(perm[4:6])
    if len(perm) == 8:
        return tuple(perm_s + sorted(perm[6:8]))
    return tuple(perm_s + list(perm[6:7]))

# sort segments of 2
segments_alphabetically_sorted_perms = map(sortperm, raw_perms)

# filter all duplicates from permutations
all_perms: list[tuple] = list(set(segments_alphabetically_sorted_perms))
# print("---------------")
# print(allowed_perms)
# print("number of allowed perms:", len(allowed_perms))
print("---------------")
# print(allowed_perms)
print("number of all perms:", len(all_perms))


def are_allowed_neighbours(perm1: tuple, perm2: tuple) -> bool:
    for i in range(0, len(perm1) - 1, 2):
        is_ok = (((perm1[i] != perm2[i]) and (perm1[i] != perm2[i + 1])) and
                 ((perm1[i + 1] != perm2[i]) and (perm1[i + 1] != perm2[i + 1])))
        if not is_ok:
            return False
    return True


def is_allowed_next_round(perm1: tuple) -> Callable[[tuple], bool]:
    def _f(perm2: tuple):
        return are_allowed_neighbours(perm1, perm2)

    return _f


class Tournament:
    maxcount: int
    rounds: list[tuple[int]] = []
    plays: dict[int, int] = {}
    pairs: set[tuple[int, int]] = set()

    def __init__(self, maxcount: int):
        self.maxcount = maxcount

    def __str__(self) -> str:
        return f"Tour[ len={self.count()}, rounds={self.rounds}, plays={self.plays} ]"

    def append_next_round(self, next_round: tuple[int, ...]) -> Self:
        new_tour = Tournament(self.maxcount)
        new_tour.rounds = self.rounds + [next_round]
        new_tour.plays =  copy.deepcopy(self.plays)
        new_tour.pairs =  copy.deepcopy(self.pairs)

        for i in range(0, len(next_round) - 1, 2):
            team1: int = next_round[i]
            team2: int = next_round[i+1]

            if i<6: # only prevent duplicate pairs for competing, not breaks
                new_tour.pairs.add((team1, team2))

            plays = new_tour.plays.get(i, {})
            if team1 in next_round[i:i+2]:
                plays[team1] = plays.get(team1, 0) + 1
            if team2 in next_round[i:i+2]:
                plays[team2] = plays.get(team2, 0) + 1
            new_tour.plays[i] = plays

        # print(new_tour)
        return new_tour

    def count(self) -> int:
        return len(self.rounds)

    def is_complete(self) -> bool:
        return self.count() == self.maxcount

    def is_empty(self) -> bool:
        return self.count() == 0

    def latest_round(self) -> tuple[int]:
        return self.rounds[len(self.rounds) - 1]

    def is_valid_next_round(self, next_round: tuple) -> bool:
        if next_round in self.rounds: return False

        if len(self.rounds)==0:
            return True

        latest_round=self.rounds[len(self.rounds)-1]
        if not are_allowed_neighbours(latest_round, next_round):
            return False
        # search for duplicate pairings (same teams play against each other twice)
        # check that noone is playing the same discipline twice - INCL BREAKS!
        for i in range(0, len(next_round), 2):
            pairing = next_round[i:i + 2]
            if pairing in self.pairs: return False

            team1 = next_round[i]
            team2 = next_round[i+1]
            for round in self.rounds:
                if team1 in round[i:i+2]:
                    if self.plays.get(i, {}).get(team1, 0) > 1: return False
                if team2 in round[i:i+2]:
                    if self.plays.get(i, {}).get(team2, 0) > 1: return False

        return True


def calc_tour(all_perms: list[tuple], current_tour: Tournament) -> list[Tournament]:
    # print("ct:", current_tour)
    if current_tour.is_complete():
        print("tour complete", current_tour)
        return [current_tour]
    # if current_tour.is_empty():
    #     next_rounds = all_perms
    # else:
    #     latest_round = current_tour.latest_round()
    #     next_rounds = filter(is_allowed_next_round(latest_round), all_perms)

    next_rounds = filter(current_tour.is_valid_next_round, all_perms)

    tours = []
    for next_round in next_rounds:
        new_tour = calc_tour(all_perms, current_tour.append_next_round(next_round))
        tours = tours + new_tour
    return tours


# p = all_perms[0]
# nbs = list(filter(is_allowed_neighbour1(), all_perms))

MAX_TOUR_SIZE = 8

seed_round = all_perms[0]

tournament = Tournament(MAX_TOUR_SIZE) #.append_next_round(tuple(seed_round))
all_tours = calc_tour(all_perms, tournament)

# print(all_tours)
print(len(all_tours))
