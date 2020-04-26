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
    def __init__(self, samples):
        self.samples = samples
        self.standard_variant = None
        self.variants = []

    class Variant:
        def __init__(self, name):
            self.name = name
            self.sum = 0
            self.min = None
            self.max = None
            self.avg = None

        def run(self, samples):
            # calculate once to initialize min/max values to increase loop perfo
            result = self.calculate()
            self.sum += result
            self.max = result
            self.min = result

            # manual calculation of the avg/min/max proved to be the fastest
            # and most effective way to gather statistics after testing
            for i in range(samples - 1):
                result = self.calculate()
                self.sum += result
                if result > self.max:
                    self.max = result
                if result < self.min:
                    self.min = result
            self.avg = self.sum / samples

        def calculate(self):
            raise NotImplementedError()

    def _percent(self, flt):
        flt *= 100
        return f"{flt:.2f}%"

    def add_variant(self, name, turn_function):
        variant = self.Variant(name)
        variant.calculate = turn_function
        self.variants.append(variant)

    def add_standard_variant(self, name, turn_function):
        variant = self.Variant(name)
        variant.calculate = turn_function
        self.standard_variant = variant

    def run(self):
        if self.standard_variant:
            self.standard_variant.run(self.samples)

        for variant in self.variants:
            variant.run(self.samples)

        self.display()

    def display(self):
        variants = [self.standard_variant]
        variants.extend(self.variants)

        columns = {
            "name:": lambda x: x.name + ":",
            "min dmg": lambda x: x.min,
            "max dmg": lambda x: x.max,
            "avg dmg:": lambda x: f"{x.avg:.4f}",
            "avg dmg gain:": lambda x: f"{x.avg - self.standard_variant.avg:.4f}",
            "percent gain:": lambda x: f"{self._percent((x.avg - self.standard_variant.avg) / x.avg)}"
        }

        col_width = max(len(variant.name) for variant in variants) + 5  # padding
        print("".join(str(column).ljust(col_width) for column in columns))
        for variant in variants:
            print("".join(str(column(variant)).ljust(col_width) for column in columns.values()))


def main():
    markaen = Character(lvl=8, dex=19, str=7, wis=17)
    feat_sampler = Sampler(10000)

    short_sword = Attack(2, d6, DEX)
    feat_sampler.add_standard_variant("no trait",
                                      lambda: markaen.attack(short_sword)
                                              + markaen.attack(short_sword)
                                      )

    avg = avg_roll(2, d6) + 3

    def savage_attacker():
        # Once per turn when you roll damage for a melee weapon attack,
        # you can reroll the weapon’s damage dice and use either total.
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

    feat_sampler.add_variant("savage attacker",
                             savage_attacker
                             )

    rapier = Attack(2, d8, DEX)
    feat_sampler.add_variant("dual wielder",
                             lambda: markaen.attack(rapier)
                                     + markaen.attack(rapier)
                             )

    short_sword = Attack(2, d6, DEX)
    green_flame_blade = Attack(1, d8)
    feat_sampler.add_variant("warlock worst case",
                             lambda: markaen.attack(short_sword)
                                     + markaen.attack(short_sword)
                                     + markaen.attack(green_flame_blade)
                             )

    short_sword = Attack(2, d6, DEX)
    green_flame_blade = Attack(1, d8)
    green_flame_blade_2nd_target = Attack(1, d8, WIS)
    feat_sampler.add_variant("warlock best case",
                             lambda: markaen.attack(short_sword)
                                     + markaen.attack(short_sword)
                                     + markaen.attack(green_flame_blade)
                                     + markaen.attack(green_flame_blade_2nd_target)
                             )

    feat_sampler.run()

    ranged_sampler = Sampler(10000)
    crossbow = Attack(1, d8, DEX)
    ranged_sampler.add_standard_variant("crossbow only",
                                        lambda: markaen.attack(crossbow)
                                        )

    eldritch_blast = Attack(1, d10)
    ranged_sampler.add_variant("eldritch blast only",
                               lambda: markaen.attack(eldritch_blast)
                                       + markaen.attack(eldritch_blast)
                               )

    ranged_sampler.run()

    spell_sampler = Sampler(10000)

    short_sword = Attack(2, d6, DEX)
    green_flame_blade = Attack(1, d8)
    spell_sampler.add_standard_variant("markaen only",
                                       lambda: markaen.attack(short_sword)
                                               + markaen.attack(short_sword)
                                               + markaen.attack(green_flame_blade)
                                       )

    wolf = Character(lvl=8, dex=15)
    bite = Attack(2, d4, DEX)
    spell_sampler.add_variant("with wolf",
                              lambda: markaen.attack(short_sword)
                                      + markaen.attack(short_sword)
                                      + markaen.attack(green_flame_blade)
                                      + wolf.attack(bite)
                                      + wolf.attack(bite)
                              )

    bestial_spirit = Character(str=18)
    maul = Attack(1, d8, STR)
    spell_sampler.add_variant("with wolf, bestial spirit",
                              lambda: markaen.attack(short_sword)
                                      + markaen.attack(short_sword)
                                      + markaen.attack(green_flame_blade)
                                      + wolf.attack(bite)
                                      + wolf.attack(bite)
                                      + bestial_spirit.attack(maul) + 2
                              )

    spell_sampler.run()


if __name__ == "__main__":
    main()
