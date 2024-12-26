# coding: utf-8
from application import db,app



class MemberComment(db.Model):
    __tablename__ = 'member_comments'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, nullable=False, index=True, server_default=db.FetchedValue(), info='??id')
    food_ids = db.Column(db.String(200), nullable=False, server_default=db.FetchedValue(), info='??ids')
    pay_order_id = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='??id')
    score = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue(), info='??')
    content = db.Column(db.String(200), nullable=False, server_default=db.FetchedValue(), info='????')
    created_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue(), info='????')

    @property
    def score_desc(self):
        score_map = {
            "10": "好评",
            "6": "中评",
            "0": "差评",
        }
        return score_map[str(self.score)]