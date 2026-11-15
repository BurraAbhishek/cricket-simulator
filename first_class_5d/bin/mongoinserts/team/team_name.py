import random


class TeamNameGenerator():

    prefixes = [
        "Dashing",
        "Eternal",
        "Defiant",
        "Valiant",
        "Shining",
        "Eclipse",
        "Dynamic",
        "Stellar",
        "Velocity",
        "Academic",
        "Iron",
    ]

    suffixes = [
        "Trailblazers",
        "Supernovas",
        "Athletes",
        "Eagles",
        "Wolves",
        "Hunters",
        "Invaders",
        "Crusaders",
        "Dynamos",
        "Strikers",
        "Legends",
        "Lions",
        "Warriors",
        "Fighters",
        "Dolphins",
        "Panthers",
        "Vipers",
        "Titans",
        "Squad"
    ]

    '''
    Some names are not allowed because:
    1. Common usage
    2. Conflicting with existing or potential teams
    '''
    prohibited_names = [
        "Dynamic Squad"
    ]
    
    def random_name(self):
        proposed_name = random.choice(self.prefixes) + " " + random.choice(self.suffixes)
        if proposed_name in self.prohibited_names:
            return self.random_name()
        return proposed_name
    
    def extended_unbound_random_name(self, size: int):
        proposed_name = self.random_name() + " " + str(size)
        return proposed_name
    
    def extended_random_name(self):
        proposed_name = self.random_name() + " "
        proposed_name += str(random.randint(2, 1000))
        return proposed_name

    def max_names(self):
        return len(self.prefixes) * (len(self.suffixes) - 1) - len(self.prohibited_names)

    def fetch_names(self, size=1, max_iterations=None):
        if size < 2:
            return [self.random_name()]
        names = []
        prefixes = []
        suffixes = []
        count = 0
        count_iters = 0
        while True:
            count_iters += 1
            chosen_name = ""
            if count < self.max_names():
                chosen_name = self.random_name()
            # elif count < 999 * self.max_names():
            #    chosen_name = self.extended_random_name()
            else:
                chosen_name = self.extended_unbound_random_name(count)
            name_selected = False
            if chosen_name not in names:
                if count >= min(len(self.prefixes), len(self.suffixes)):
                    names.append(chosen_name)
                    name_selected = True
                else:
                    name_components = chosen_name.split(" ")
                    if name_components[0] not in prefixes and name_components[1] not in suffixes:
                        names.append(chosen_name)
                        prefixes.append(name_components[0])
                        suffixes.append(name_components[1])
                        name_selected = True
            if count >= size:
                return names
            if max_iterations is not None:
                if count_iters > max_iterations:
                    return names
            if name_selected:
                count += 1

