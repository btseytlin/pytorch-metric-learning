#! /usr/bin/env python3

from .base_miner import BaseTupleMiner
from ..utils import loss_and_miner_utils as lmu
import torch


class PairMarginMiner(BaseTupleMiner):
    """
    Returns positive pairs that have distance greater than a margin and negative
    pairs that have distance less than a margin
    """

    def __init__(
        self, pos_margin, neg_margin, use_similarity, squared_distances=False, **kwargs
    ):
        super().__init__(**kwargs)
        self.pos_margin = pos_margin
        self.neg_margin = neg_margin
        self.use_similarity = use_similarity
        self.squared_distances = squared_distances
        self.add_to_recordable_attributes(list_of_names=["pos_pair_dist", "neg_pair_dist"], is_stat=True)

    def mine(self, embeddings, labels, ref_emb, ref_labels):
        mat = lmu.get_pairwise_mat(embeddings, ref_emb, self.use_similarity, self.squared_distances)
        a1, p, a2, n = lmu.get_all_pairs_indices(labels, ref_labels)
        pos_pair = mat[a1, p]
        neg_pair = mat[a2, n]
        self.pos_pair_dist = torch.mean(pos_pair).item() if len(pos_pair) > 0 else 0
        self.neg_pair_dist = torch.mean(neg_pair).item() if len(neg_pair) > 0 else 0
        pos_mask_condition = self.pos_filter(pos_pair, self.pos_margin)
        neg_mask_condition = self.neg_filter(neg_pair, self.neg_margin)
        a1 = torch.masked_select(a1, pos_mask_condition)
        p = torch.masked_select(p, pos_mask_condition)
        a2 = torch.masked_select(a2, neg_mask_condition)
        n = torch.masked_select(n, neg_mask_condition)
        return a1, p, a2, n

    def pos_filter(self, pos_pair, margin):
        return pos_pair < margin if self.use_similarity else pos_pair > margin

    def neg_filter(self, neg_pair, margin):
        return neg_pair > margin if self.use_similarity else neg_pair < margin
