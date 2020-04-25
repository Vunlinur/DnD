import inspect
import random

DEBUG = False

STR = "str"
DEX = "dex"
CON = "con"
INT = "int"
WIS = "wis"
CHA = "cha"

scores = [STR, DEX, CON, INT, WIS, CHA, None]

d4 = 4
d6 = 6
d8 = 8
d10 = 10
d12 = 12
d20 = 20


def roll_die(size):
    result = random.randint(1, size)
    if DEBUG: print(f"rolled {result} on d{size}")
    return result


def roll(quantity, dice):
    sum = 0
    for times in range(quantity):
        sum += roll_die(dice)
    return sum


def avg_roll(quantity, dice):
    return quantity * ((1 + dice) / 2)


class Character:
    def score_bonus(self, score):
        return int(score / 2) - 5
        # TODO add proficiency bonus for skills the char is proficient with

    def proficiency_bonus(self, level):
        return int((level - 1) / 4) + 2

    def __init__(self, lvl=1, str=10, dex=10, con=10, int=10, wis=10, cha=10):
        self.lvl = lvl
        self.str = str
        self.dex = dex
        self.con = con
        self.int = int
        self.wis = wis
        self.cha = cha
        self.prof_bonus = self.proficiency_bonus(self.lvl)

    def attack(self, attack):
        if attack.type:
            ability_score = self.__getattribute__(attack.type)
            ability_modifier = self.score_bonus(ability_score)
        else:
            ability_modifier = 0
        return attack.execute() + ability_modifier


class Attack:
    def __init__(self, quantity, dice, base=None):
        if base not in scores:
            raise Exception("Unknown Attack kind")
        self.type = base
        self.quantity = quantity
        self.dice = dice

    def execute(self):
        return roll(self.quantity, self.dice)


class Sampler:
    def __init__(self, name, samples):
        self.name = name
        self.samples = samples
        self.sum = 0
        self.standard = None

    def _percent(self, flt):
        flt *= 100
        return f"{flt:.2f}%"

    def run(self):
        for i in range(self.samples):
            self.sum += self.calculate()
        self.avg = self.sum/self.samples

    def summarize(self):
        col_width = 24
        if self.standard:
            summary = [self.name + ":",
                       "avg:", f"{self.avg:.4f}",
                       "avg gain:", f"{self.avg - self.standard:.4f}",
                       "percent gain:", f"{self._percent((self.avg - self.standard) / self.avg)}"]
        else:
            summary = [self.name + ":",
                       "avg:", f"{self.avg:.4f}"]
        print("".join(str(column).ljust(col_width) for column in summary))

    def calculate(self):
        raise NotImplementedError()


def main():
    turns = 10000
    markaen = Character(lvl=8, dex=19, str=7, wis=17)

    # no trait
    sampler = Sampler("no trait", turns)
    short_sword = Attack(2, d6, DEX)
    sampler.calculate = lambda: markaen.attack(short_sword)\
                                + markaen.attack(short_sword)
    sampler.run()
    sampler.summarize()

    std = sampler.avg

    # savage attacker
    avg = avg_roll(2, d6) + 3
    short_sword = Attack(2, d6, DEX)

    def savage_attacker():
        # Once per turn when you roll damage for a melee weapon attack, you can reroll the weapon’s damage dice and use either total.
        reroll = 0

        att_1 = markaen.attack(short_sword)
        if att_1 <= avg:
            reroll = markaen.attack(short_sword)
            att_1 = reroll if reroll > att_1 else att_1

        att_2 = markaen.attack(short_sword)
        if not reroll:
            reroll = markaen.attack(short_sword)
            att_2 = reroll if reroll > att_2 else att_2

        return att_1 + att_2

    sampler = Sampler("savage attacker", turns)
    sampler.standard = std
    sampler.calculate = savage_attacker
    sampler.run()
    sampler.summarize()

    # dual wielder
    sampler = Sampler("dual wielder", turns)
    sampler.standard = std
    rapier = Attack(2, d8, DEX)
    sampler.calculate = lambda: markaen.attack(rapier)\
                                + markaen.attack(rapier)
    sampler.run()
    sampler.summarize()

    # magic initiate warlock worst case
    sampler = Sampler("warlock worst case", turns)
    sampler.standard = std
    short_sword = Attack(2, d6, DEX)
    green_flame_blade = Attack(1, d8)
    sampler.calculate = lambda: markaen.attack(short_sword)\
                                + markaen.attack(short_sword)\
                                + markaen.attack(green_flame_blade)
    sampler.run()
    sampler.summarize()

    # magic initiate warlock best case
    sampler = Sampler("warlock best case", turns)
    sampler.standard = std
    short_sword = Attack(2, d6, DEX)
    green_flame_blade = Attack(1, d8)
    green_flame_blade_2nd_target = Attack(1, d8, WIS)
    sampler.calculate = lambda: markaen.attack(short_sword)\
                                + markaen.attack(short_sword)\
                                + markaen.attack(green_flame_blade)\
                                + markaen.attack(green_flame_blade_2nd_target)
    sampler.run()
    sampler.summarize()

    # crossbow only
    sampler = Sampler("crossbow only", turns)
    crossbow = Attack(1, d8, DEX)
    sampler.calculate = lambda: markaen.attack(crossbow)
    sampler.run()
    sampler.summarize()

    ranged_std = sampler.avg

    # eldritch blast only
    sampler = Sampler("eldritch blast only", turns)
    sampler.standard = ranged_std
    eldritch_blast = Attack(1, d10)
    sampler.calculate = lambda: markaen.attack(eldritch_blast)\
                                + markaen.attack(eldritch_blast)
    sampler.run()
    sampler.summarize()

if __name__ == "__main__":
    main()