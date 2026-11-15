class Partnership():

    def __init__(self, b1, b2=None) -> None:
        if b2 is not None:
            partnership_id = str(sorted([b1, b2]))
            self.id = partnership_id
            self.p1 = b1
            self.p2 = b2
            self.p1_runs = 0
            self.p2_runs = 0
            self.p1_balls = 0
            self.p2_balls = 0
            self.extra = 0
        elif isinstance(b1, dict):
            self.id = b1.get("_id")
            self.from_dict(b1)

    def from_dict(self, partnership: dict):
        if partnership.get("p1") is not None:
            self.p1 = partnership.get("p1")
        if partnership.get("p2") is not None:
            self.p2 = partnership.get("p2")
        self.p1_runs = partnership.get("p1_runs", 0)
        self.p2_runs = partnership.get("p2_runs", 0)
        self.p1_balls = partnership.get("p1_balls", 0)
        self.p2_balls = partnership.get("p2_balls", 0)
    
    def as_dict(self):
        return {
            "_id": self.id,
            "p1": self.p1,
            "p2": self.p2,
            "p1_runs": self.p1_runs,
            "p2_runs": self.p2_runs,
            "p1_balls": self.p1_balls,
            "p2_balls": self.p2_balls,
            "extra": 0
        }
