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


class Round:
    round: tuple[int, ...]
    handball: tuple[int, int]
    turmball: tuple[int, int]
    parcours: tuple[int, int]
    pause: tuple[int, int]

    def __init__(self, round: tuple[int, ...]):
        self.round = round
        self.handball = round[0:2]
        self.turmball = round[2:4]
        self.parcours = round[4:6]
        self.pause = round[6:8]

    def __str__(self) -> str:
        return f"Round[ {self.round} ]"

    def are_allowed_neighbours(self, other: Self) -> bool:
        perm1 = self.round
        perm2 = other.round
        for i in range(0, len(perm1) - 1, 2):
            is_ok = (((perm1[i] != perm2[i]) and (perm1[i] != perm2[i + 1])) and
                     ((perm1[i + 1] != perm2[i]) and (perm1[i + 1] != perm2[i + 1])))
            if not is_ok:
                return False

        return True


class Tournament:
    maxcount: int
    rounds: list[Round] = []
    plays: dict[int, int] = {}
    seen_pairings: set[tuple[int, int]] = set()

    def __init__(self, maxcount: int):
        self.maxcount = maxcount

    def __str__(self) -> str:
        return f"Tour[ len={self.count()}, rounds={[ r.round for r in self.rounds]}, plays={self.plays} ]"

    def append_next_round(self, next_round: Round) -> Self:
        new_tour = Tournament(self.maxcount)
        new_tour.rounds = self.rounds + [next_round]
        new_tour.plays = copy.deepcopy(self.plays)
        new_tour.seen_pairings = copy.deepcopy(self.seen_pairings)

        # record seen pairings
        new_tour.seen_pairings.add(next_round.handball)
        new_tour.seen_pairings.add(next_round.parcours)
        new_tour.seen_pairings.add(next_round.turmball)

        for i, pair in enumerate([next_round.handball, next_round.parcours, next_round.turmball]):
            team1: int = pair[0]
            team2: int = pair[1]
            plays = new_tour.plays.get(i, {})
            plays[team1] = plays.get(team1, 0) + 1
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

    def latest_round(self) -> Round:
        return self.rounds[len(self.rounds) - 1]

    def is_valid_next_round(self, next_round: Round) -> bool:
        if next_round in self.rounds: return False

        if len(self.rounds) == 0:
            return True

        if next_round.handball in self.seen_pairings: return False
        if next_round.turmball in self.seen_pairings: return False
        if next_round.parcours in self.seen_pairings: return False

        latest_round = self.rounds[len(self.rounds) - 1]
        if not latest_round.are_allowed_neighbours(next_round):
            return False

        # search for duplicate pairings (same teams play against each other twice)
        # check that noone is playing the same discipline twice - INCL BREAKS!
        for i, pair in enumerate([next_round.handball, next_round.parcours, next_round.turmball]):
            team1: int = pair[0]
            team2: int = pair[1]
            plays = self.plays.get(i, {})
            if plays.get(team1, 0) > 1: return False
            if plays.get(team2, 0) > 1: return False

        return True


def calc_tour(all_rounds: list[Round], current_tour: Tournament) -> list[Tournament]:
    # print("ct:", current_tour)
    if current_tour.is_complete():
        print("tour complete", current_tour)
        return [current_tour]

    next_rounds = filter(current_tour.is_valid_next_round, all_rounds)

    tours = []
    for next_round in next_rounds:
        new_tour = calc_tour(all_rounds, current_tour.append_next_round(next_round))
        tours = tours + new_tour
    return tours


# p = all_perms[0]
# nbs = list(filter(is_allowed_neighbour1(), all_perms))

MAX_TOUR_SIZE = 8

all_rounds: list[Round] = [Round(perm) for perm in all_perms]
tournament = Tournament(MAX_TOUR_SIZE)  # .append_next_round(tuple(seed_round))
all_tours = calc_tour(all_rounds, tournament)

# print(all_tours)
print(len(all_tours))
