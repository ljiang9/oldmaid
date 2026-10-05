#!/usr/bin/env python3
"""oldmaid - 终端抽鬼牌(Old Maid)游戏:你 vs 电脑。

规则:去掉一张 Q,剩余 51 张(含 3 张 Q)。先各自丢掉手中的对子,
然后轮流从对方手中抽一张,凑成对子就丢掉。三张 Q 中必有一张落单,
最后手里剩这张落单 Q(鬼牌)者输。
"""
import argparse
import random
import secrets
import sys

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]
REMOVED_QUEEN = ("Q", "♠")  # 从牌堆拿掉的一张 Q(黑桃 Q);剩下的 3 张 Q 中落单者为鬼牌

CN_RANK = {"A": "A", "J": "J", "Q": "Q", "K": "K"}


def card_name(card):
    r, s = card
    return f"{s}{r}"


def build_deck(rng):
    """51 张牌:去掉黑桃 Q。"""
    deck = [(r, s) for r in RANKS for s in SUITS if (r, s) != REMOVED_QUEEN]
    rng.shuffle(deck)
    return deck


def discard_pairs(hand):
    """丢掉所有对子(同点数两张),返回(剩余手牌, 丢掉的对数)。"""
    by_rank = {}
    for c in hand:
        by_rank.setdefault(c[0], []).append(c)
    kept, pairs = [], 0
    for cards in by_rank.values():
        pairs += len(cards) // 2
        kept.extend(cards[: len(cards) % 2])
    return kept, pairs


def deal(deck):
    you = sorted(deck[0::2])
    ai = sorted(deck[1::2])
    return you, ai


def draw_from(hand_from, idx):
    """从对方手牌取走第 idx 张,返回(牌, 新手牌)。"""
    card = hand_from[idx]
    return card, hand_from[:idx] + hand_from[idx + 1:]


class Game:
    def __init__(self, seed=None):
        self.rng = random.Random(seed) if seed is not None else secrets.SystemRandom()
        deck = build_deck(self.rng)
        you, ai = deal(deck)
        self.you, d1 = discard_pairs(you)
        self.ai, d2 = discard_pairs(ai)
        self.log = [f"初始丢对子:你丢 {d1} 对,电脑丢 {d2} 对。"]
        self.turn_you = True  # 你先抽

    def over(self):
        return not self.you or not self.ai

    def loser(self):
        """返回 'you' / 'ai' / None。终局时必剩一张落单的 Q,持有者输。"""
        if not self.over():
            return None
        if len(self.you) == 1 and self.you[0][0] == "Q":
            return "you"
        if len(self.ai) == 1 and self.ai[0][0] == "Q":
            return "ai"
        return None

    def step(self, pick_idx=None):
        """走一步。你的回合需给 pick_idx(电脑手牌位置);电脑回合随机抽。"""
        if self.over():
            return None
        if self.turn_you:
            if pick_idx is None or not (0 <= pick_idx < len(self.ai)):
                raise ValueError("请选择电脑手牌的有效位置")
            card, self.ai = draw_from(self.ai, pick_idx)
            self.you.append(card)
            who = "你"
        else:
            pick_idx = self.rng.randrange(len(self.you))
            card, self.you = draw_from(self.you, pick_idx)
            self.ai.append(card)
            who = "电脑"
        # 抽到后立即丢对子
        if self.turn_you:
            self.you, n = discard_pairs(self.you)
        else:
            self.ai, n = discard_pairs(self.ai)
        self.log.append(f"{who}抽到 {card_name(card)}, 丢掉 {n} 对。")
        self.turn_you = not self.turn_you
        return card

    def auto(self):
        """自动对战:双方都随机抽。"""
        while not self.over():
            if self.turn_you:
                self.step(self.rng.randrange(len(self.ai)))
            else:
                self.step()


def play_interactive(seed=None):
    g = Game(seed)
    print("抽鬼牌 Old Maid | 51 张牌(去掉一张 Q,落单的 Q 为鬼牌)")
    print("".join(g.log))
    while not g.over():
        print(f"\n你的手牌({len(g.you)} 张): " + " ".join(card_name(c) for c in g.you))
        if g.turn_you:
            print(f"电脑手牌: {'? ' * len(g.ai)}({len(g.ai)} 张), 选 1-{len(g.ai)} 抽一张 (q 退出)")
            raw = input("> ").strip()
            if raw.lower() == "q":
                print("已退出。")
                return
            try:
                idx = int(raw) - 1
                if not (0 <= idx < len(g.ai)):
                    raise ValueError
            except ValueError:
                print("输入无效,请输入 1 到", len(g.ai), "的数字。")
                continue
            g.step(idx)
        else:
            g.step()
        print(g.log[-1])
    loser = g.loser()
    print("\n" + ("😱 你手里剩鬼牌,你输了!" if loser == "you" else "🎉 电脑剩鬼牌,你赢了!"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="抽鬼牌 Old Maid:你 vs 电脑")
    ap.add_argument("--auto", type=int, default=0, metavar="N",
                    help="自动模拟 N 局并统计胜率")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    args = ap.parse_args(argv)
    if args.auto:
        if args.auto <= 0:
            ap.error("--auto 需要正整数")
        wins = losses = 0
        rng = random.Random(args.seed)
        for _ in range(args.auto):
            g = Game(rng.randrange(2**31))
            g.auto()
            loser = g.loser()
            if loser == "ai":
                wins += 1
            elif loser == "you":
                losses += 1
        print(f"模拟 {args.auto} 局:你赢 {wins} 局,电脑赢 {losses} 局")
        return
    if not sys.stdin.isatty():
        print("error: 交互模式需要终端,请用 --auto 模拟。", file=sys.stderr)
        sys.exit(2)
    play_interactive(args.seed)


if __name__ == "__main__":
    main()
