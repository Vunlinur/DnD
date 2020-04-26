import inspect
import random
import time


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


class Variant:
    def __init__(self, name, samples):
        self.name = name
        self.samples = samples
        self.sum = 0
        self.min = None
        self.max = None
        self.avg = None
        self.standard = None

    def _percent(self, flt):
        flt *= 100
        return f"{flt:.2f}%"

    def run(self):
        # calculate once to initialize min/max values to increase loop perfo
        result = self.calculate()
        self.sum += result
        self.max = result
        self.min = result

        # manual calculation of the avg/min/max proved to be the fastest
        # and most effective way to gather statistics after testing
        for i in range(self.samples-1):
            result = self.calculate()
            self.sum += result
            if result > self.max:
                self.max = result
            if result < self.min:
                self.min = result
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
    variant = Variant("no trait", turns)
    short_sword = Attack(2, d6, DEX)
    variant.calculate = lambda: markaen.attack(short_sword)\
                                + markaen.attack(short_sword)
    variant.run()
    variant.summarize()

    std = variant.avg

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

    variant = Variant("savage attacker", turns)
    variant.standard = std
    variant.calculate = savage_attacker
    variant.run()
    variant.summarize()

    # dual wielder
    variant = Variant("dual wielder", turns)
    variant.standard = std
    rapier = Attack(2, d8, DEX)
    variant.calculate = lambda: markaen.attack(rapier)\
                                + markaen.attack(rapier)
    variant.run()
    variant.summarize()

    # magic initiate warlock worst case
    variant = Variant("warlock worst case", turns)
    variant.standard = std
    short_sword = Attack(2, d6, DEX)
    green_flame_blade = Attack(1, d8)
    variant.calculate = lambda: markaen.attack(short_sword)\
                                + markaen.attack(short_sword)\
                                + markaen.attack(green_flame_blade)
    variant.run()
    variant.summarize()

    # magic initiate warlock best case
    variant = Variant("warlock best case", turns)
    variant.standard = std
    short_sword = Attack(2, d6, DEX)
    green_flame_blade = Attack(1, d8)
    green_flame_blade_2nd_target = Attack(1, d8, WIS)
    variant.calculate = lambda: markaen.attack(short_sword)\
                                + markaen.attack(short_sword)\
                                + markaen.attack(green_flame_blade)\
                                + markaen.attack(green_flame_blade_2nd_target)
    variant.run()
    variant.summarize()

    # crossbow only
    variant = Variant("crossbow only", turns)
    crossbow = Attack(1, d8, DEX)
    variant.calculate = lambda: markaen.attack(crossbow)
    variant.run()
    variant.summarize()

    ranged_std = variant.avg

    # eldritch blast only
    variant = Variant("eldritch blast only", turns)
    variant.standard = ranged_std
    eldritch_blast = Attack(1, d10)
    variant.calculate = lambda: markaen.attack(eldritch_blast)\
                                + markaen.attack(eldritch_blast)
    variant.run()
    variant.summarize()

if __name__ == "__main__":
    main()