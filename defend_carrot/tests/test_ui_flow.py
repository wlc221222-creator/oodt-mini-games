"""Real menu, pause, guide, selection, upgrade and eight-stage transition events."""
import os
from pathlib import Path
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
import config as C
from game import Game
from entities import Apple,tile_center


def main():
    g=Game()
    try:
        def key(value):
            g.handle_event(pygame.event.Event(pygame.KEYDOWN,key=value))
        def click(rect):
            g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center))
        assert g.state=='menu'
        key(pygame.K_l)
        assert g.level_select_open
        click(g.ui.level_rect(7))
        assert g.level_select_open and g.state=='menu'
        key(pygame.K_ESCAPE)
        click(g.ui.secondary_rect)
        assert g.guide_open
        key(pygame.K_TAB)
        assert g.guide.tab=='monsters'
        key(pygame.K_ESCAPE)
        click(g.ui.primary_rect)
        assert g.state=='playing' and g.level_index==0
        key(pygame.K_8)
        assert g.selected is None and g.notice
        click(g._card_rect(0))
        assert g.selected==C.SHOP_ORDER[0]
        key(pygame.K_p)
        snapshot=(g.elapsed,g.wave_timer,g.coins,g.selected)
        g.update(10);key(pygame.K_8);g.draw()
        assert snapshot==(g.elapsed,g.wave_timer,g.coins,g.selected)
        key(pygame.K_p)
        key(pygame.K_TAB)
        assert g.speed_multiplier==2
        key(pygame.K_i);key(pygame.K_TAB)
        assert g.speed_multiplier==2
        key(pygame.K_ESCAPE)
        g.speed_multiplier=1
        for index in range(len(C.LEVELS)):
            assert g.level_index==index
            col,row=next((c,r) for r in range(C.GRID_ROWS) for c in range(C.GRID_COLS) if g.can_build(c,r))
            g.selected='apple';g._on_click(tile_center(col,row))
            assert len(g.fruits)==1
            g._on_click(tile_center(col,row))
            assert g.inspected is g.fruits[0]
            tower=g.inspected;g.coins=tower.upgrade_cost
            click(g.ui.upgrade_rect)
            assert tower.level==2 and g.coins==0
            value=tower.sell_value;click(g.ui.sell_rect)
            assert not g.fruits and g.coins==value
            g.score,g.kills,g.coins=77,5,9999
            g.wave_index=len(C.LEVELS[index]['waves'])-1
            g.spawn_queue=[];g.monsters=[]
            g.update(1/60);g.draw()
            assert g.state==('won' if index==len(C.LEVELS)-1 else 'levelclear')
            assert g.progress['best'][str(index)]==3
            if index<len(C.LEVELS)-1:
                click(g.ui.primary_rect)
                assert g.coins==C.LEVELS[index+1]['start_coins']+C.PASSIVE_INCOME
                assert (g.score,g.kills,g.carrot.hp)==(77,5,3)
                assert not g.fruits and g.available_towers==C.LEVELS[index+1]['towers']
        click(g.ui.secondary_rect)
        assert g.state=='menu'
        key(pygame.K_l);click(g.ui.level_rect(0))
        assert g.state=='playing' and g.level_index==0
        print('PASS: eight-stage menus, locks, guide tabs, pause, speed, upgrade/sell and independent stage budgets')
    finally:
        pygame.quit()


if __name__=='__main__':
    main()
