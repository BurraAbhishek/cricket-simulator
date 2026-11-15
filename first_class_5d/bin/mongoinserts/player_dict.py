from bin.models.team import TeamCollection, AbstractPlayer


def get_replacer_dict():
    final_dict = {}
    teams = TeamCollection()
    for i in teams.find():
        t0 = teams.get(i)
        k0: str = t0.abstract_name()
        v0: str = t0.name()
        final_dict[k0] = v0
        k0 = k0.upper()
        v0 = v0.upper()
        final_dict[k0] = v0
        members = t0.members()
        for j in members:
            k = j.get("_id")
            k1 = AbstractPlayer(j).abstract_name()
            k2 = "{{" + k + ".nickname" + "}}"
            final_dict[k1] = j.get("name")
            final_dict[k2] = j.get("nickname", j.get("name"))
    return final_dict
