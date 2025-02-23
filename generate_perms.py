#!/usr/bin/env python3

import itertools
import copy
import random
from typing import Self
import time

timestamp_start = int(time.time() * 1000.0)


class Round:
    competitions: list[tuple[int, int]]
    pause: tuple[int, int]

    def __init__(self, round: tuple[int, ...]):
        self.round = round
        self.competitions = [p for p in itertools.batched(round, 2)]
        self.pause = tuple(self.competitions.pop())
        return

    def __repr__(self) -> str:
        return f"Round(({self.round}))"

    def __lt__(self, other: Self) -> bool:
        return self.round < other.round

    def record_seen_pairings(self, seen: set[tuple[int, int]]):
        seen.update(self.competitions)
        seen.update([self.pause])
        return

    def has_seen_pairings(self, seen: set[tuple[int, int]]):
        # return len(set(self.competitions) & seen) > 0
        return next((True for comp in (self.competitions+[self.pause]) if comp in seen), False)

    def record_plays(self, all_plays: dict[int, dict[int, int]]):
        for comp_ix, pair in enumerate(self.competitions):
            plays = all_plays.get(comp_ix, {})
            for team in pair:
                plays[team] = plays.get(team, 0) + 1
            all_plays[comp_ix] = plays

    def exceeds_max_plays(self, all_plays: dict[int, dict[int, int]]):
        """
        search for duplicate pairings (same teams play against each other twice)
        check that noone is playing the same discipline more than twice - INCL BREAKS!
        """
        for comp_ix, pair in enumerate(self.competitions):
            plays = all_plays.get(comp_ix, {})
            # for team in pair:
            if plays.get(pair[0], 0) > 1: return True
            if plays.get(pair[1], 0) > 1: return True
        return False

    def is_allowed_next_round(self: Self, next: Self) -> bool:
        """ NO team must compete twice in a row in same competition """

        perm1 = self.round
        perm2 = next.round

        teams_count = len(perm1)
        ix_last = len(perm1) - 1
        # with an uneven number of teams, we must check "pause" comp separately
        if ((teams_count % 2 == 1)
                and (perm1[ix_last] == perm2[ix_last])):
            return False

        for i in range(0, len(perm1) - 1, 2):
            is_ok = (((perm1[i] != perm2[i]) and (perm1[i] != perm2[i + 1])) and
                     ((perm1[i + 1] != perm2[i]) and (perm1[i + 1] != perm2[i + 1])))
            if not is_ok:
                return False

        return True

        # # pair each competition from this round with next
        # comp_pairs = [comp_pair for comp_pair in
        #               zip(self.competitions + [self.pause], next.competitions + [next.pause])]
        # # calc length of intersection for each pair and sum -> must be 0 if no overlaps
        # overlaps = sum([len(set(comp_pair[0]) & set(comp_pair[1])) for comp_pair in comp_pairs])
        # return overlaps == 0


class Tournament:
    max_rounds: int
    rounds: list[Round] = []
    plays: dict[int, dict[int, int]] = {}
    seen_pairings: set[tuple[int, int]] = set()

    def __init__(self, maxcount: int, teams_count: int):
        self.max_rounds = maxcount
        self.teams_count = teams_count

    def __str__(self) -> str:
        return f"Tour[ len={self.count()}, rounds={[r.round for r in self.rounds]}, plays={self.plays} ]"

    def append_next_round(self, next_round: Round) -> Self:
        new_tour = Tournament(self.max_rounds, self.teams_count)
        new_tour.rounds = self.rounds + [next_round]
        new_tour.plays = copy.deepcopy(self.plays)
        new_tour.seen_pairings = self.seen_pairings.copy()

        next_round.record_seen_pairings(new_tour.seen_pairings)
        next_round.record_plays(new_tour.plays)

        # print(new_tour)
        return new_tour

    def count(self) -> int:
        return len(self.rounds)

    def is_complete(self) -> bool:
        return self.count() == self.max_rounds

    def is_empty(self) -> bool:
        return self.count() == 0

    def latest_round(self) -> Round:
        return self.rounds[len(self.rounds) - 1]

    def has_min_plays(self):
        """
        """
        for comp_plays in self.plays.values():
            for team in range(1, self.teams_count):
                # plays = comp_plays.get(team, {})
                if comp_plays.get(team, 0) < 2: return False
        return True

    @staticmethod
    def are_consecutive_with_pause(r1: Round, r2: Round, cur: Round):
        # with less than 8 teams we must not enforce a gap of 2 rounds between each comp for each team
        # if len(r2.round) < 8:
        #     # only check for paused teams and last competition ("parcours"), i.e. no team faces parcours-pause-parcours
        #     for team in r2.pause:
        #         # if team in r1.competitions[-1] and team in cur.competitions[-1]: return True
        #         for ix, _ in enumerate(r2.competitions[1:]): # only seems to find solutions if at least 1 comp is "free"
        #             if team in r1.competitions[ix] and team in cur.competitions[ix]: return True
        #     return False

        for team in r2.pause:
            if team in r1.competitions[-1] and team in cur.competitions[-1]: return True
            # for ix, _ in enumerate(r2.competitions):
            #     if team in r1.competitions[ix] and team in cur.competitions[ix]: return True
        return False

    def is_valid_next_round(self, next_round: Round) -> bool:
        if next_round in self.rounds: return False

        if next_round.has_seen_pairings(self.seen_pairings):
            return False

        if len(self.rounds) == 0:
            return True

        latest_round = self.rounds[len(self.rounds) - 1]
        if not latest_round.is_allowed_next_round(next_round):
            return False

        if len(self.rounds) > 1:
            before_latest_round = self.rounds[len(self.rounds) - 2]
            if self.are_consecutive_with_pause(before_latest_round, latest_round, next_round):
                return False

        if next_round.exceeds_max_plays(self.plays):
            return False

        return True


class CalcContext:
    tours_checked = 0
    max_rounds = 0


def calc_tour(ctx: CalcContext, all_rounds: list[Round], current_tour: Tournament) -> list[Tournament]:
    # print("ct:", current_tour)
    if current_tour.is_complete():
        # if not current_tour.has_min_plays():
        #     # print(int(time.time() * 1000.0) - timestamp_start, "ms: tour invalid: ", current_tour)
        #     return []
        print(int(time.time() * 1000.0) - timestamp_start, "ms: tour complete ", current_tour)
        return [current_tour]

    found_tours = []
    for next_round in all_rounds:
        if current_tour.is_valid_next_round(next_round):
            found_tours.extend(calc_tour(ctx, all_rounds, current_tour.append_next_round(next_round)))
            if (len(found_tours)) > 0:
                return found_tours

    # print("completed:", current_tour, ", children: ", len(found_tours))
    ctx.tours_checked += 1
    ctx.max_rounds = max(current_tour.count(), ctx.max_rounds)
    print("\033[1;1Htours-checked:", ctx.tours_checked, ", max rounds: ", ctx.max_rounds, "   ")
    return found_tours


def calc_all_permutations(seed_round: tuple[int, ...]):
    raw_perms = list(itertools.permutations(seed_round))
    print("number of raw perms:", len(raw_perms))

    # sort segments of 2
    def sortperm(perm: tuple) -> tuple:
        pairings = [sorted(p) for p in itertools.batched(perm, 2)]
        return tuple(itertools.chain.from_iterable(pairings))

    segments_alphabetically_sorted_perms = map(sortperm, raw_perms)

    # filter all duplicates from permutations
    all_perms: set[tuple] = set(segments_alphabetically_sorted_perms)
    print("---------------")
    print("number of all perms:", len(all_perms))

    all_rounds: list[Round] = [Round(perm) for perm in all_perms]
    # all_rounds = sorted(all_rounds)
    random.shuffle(all_rounds)
    return all_rounds


avoid_handball_pairings = {
    # (1, 5), (2, 5), (1, 8), (2, 8), (1, 9), (2, 9),
    # (1, 2), (1, 3), (2, 3), (4, 5), (6, 7), (6, 8), (7, 8)
    # (2, 8), (4, 5), (1, 3), (6, 7), (3, 4), (2, 5), (6, 8), (1, 7),  # Betzingen
    # (3, 8), (1, 2), (4, 7), (5, 6), (1, 7), (2, 4), (5, 8), (4, 6),  # Ehningen
    # (1, 6), (7, 8), (2, 4), (3, 5), (1, 8), (4, 6), (5, 7), (2, 4),  # Pfullingen
}
avoid_turmball_pairings = {
    # (1, 5), (2, 5), (1, 8), (2, 8), (1, 9), (2, 9),
    # (1, 2), (1, 3), (2, 3), (4, 5), (6, 7), (6, 8), (7, 8)
    # (4, 7), (3, 6), (5, 8), (1, 2), (6, 7), (1, 8), (2, 3), (4, 5),  # Betzingen
    # (4, 5), (6, 8), (1, 3), (2, 7), (4, 8), (1, 5), (2, 6), (3, 7),  # Ehningen
    # (2, 8), (4, 5), (1, 3), (6, 7), (3, 4), (2, 5), (6, 8), (1, 7),  # Pfullingen
}

avoid_parcours_pairings = {
    # (1, 5), (2, 5), (1, 8), (2, 8), (1, 9), (2, 9)
    # (1,2), (4,5), (6,7), (6,8)
    # (1, 6), (5, 7), (2, 8), (3, 4), (5, 6), (4, 8), (3, 7), (1, 2)  # Ehningen
}


def shall_avoid_pairing(r: Round):
    return (
            (not r.competitions[0] in avoid_handball_pairings) and
            (not r.competitions[1] in avoid_turmball_pairings) and
            (not r.competitions[2] in avoid_parcours_pairings)
    )


seed_round = (1, 2, 3, 4, 5, 6, 7, 8, 9)
MAX_TOUR_SIZE = len(seed_round)

all_rounds = calc_all_permutations(seed_round)
all_rounds = list(filter(shall_avoid_pairing, all_rounds))
print(f"allowed perms: {len(all_rounds)}")

tournament = Tournament(MAX_TOUR_SIZE, len(seed_round))
ctx = CalcContext()
all_tours = calc_tour(ctx, all_rounds, tournament)

# print(all_tours)
print(len(all_tours))
print(int(time.time() * 1000.0) - timestamp_start, "ms: finished")
