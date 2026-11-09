"""Exercise a complete opening stage through the real game and purchase rules."""
from test_campaign_balance import run
import pygame
import config as C


def main():
    game=run(0)
    assert game.state=='levelclear' and game.carrot.hp>0
    assert game.kills==sum(map(len,C.LEVELS[0]['waves']))
    game._continue()
    assert game.level_index==1 and game.carrot.hp==3
    assert game.coins==C.LEVELS[1]['start_coins']+C.PASSIVE_INCOME
    print('PASS: complete opening stage and independent second-stage startup')
    pygame.quit()


if __name__=='__main__':
    main()
