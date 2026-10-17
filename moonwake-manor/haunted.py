#!/usr/bin/env python3
"""Moonwake Manor v6: fixed 800x480 software-composited haunted display."""
import argparse, json, math, os, signal, time
from pathlib import Path
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
os.environ.setdefault('SDL_VIDEO_ALLOW_SCREENSAVER','0')
import pygame
from timeline import Timeline
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--windowed',action='store_true'); p.add_argument('--demo',action='store_true')
    p.add_argument('--fps',type=int,choices=range(10,31),default=15)
    p.add_argument('--seed',type=int); p.add_argument('--no-flashes',action='store_true')
    p.add_argument('--seconds',type=float,default=0); p.add_argument('--headless',action='store_true')
    p.add_argument('--snapshot',type=Path); p.add_argument('--fast-test',action='store_true')
    p.add_argument('--all-lights',action='store_true',help='Inspect all room masks')
    p.add_argument('--silhouette-room',type=int,choices=range(4),help='Inspect a human upstairs silhouette')
    p.add_argument('--event',choices=('windows','door','shadow'),help='Preview one major event immediately')
    p.add_argument('--no-startup-showtime',action='store_true',help='Skip the one-time haunting 15 seconds after startup')
    a=p.parse_args()
    if a.fast_test and a.seconds<=0: p.error('--fast-test requires --seconds > 0')
    if a.headless: os.environ['SDL_VIDEODRIVER']='dummy'
    pygame.display.init()
    screen=pygame.display.set_mode((800,480),0 if a.windowed or a.headless else pygame.FULLSCREEN)
    pygame.display.set_caption('Moonwake Manor'); pygame.mouse.set_visible(False)
    cfg=json.loads((ROOT/'assets/scene.json').read_text(encoding='utf-8-sig'))
    def load(name,alpha=True):
        s=pygame.image.load(str(ROOT/'assets'/name))
        return s.convert_alpha() if alpha else s.convert()
    bg=load('background.png',False)
    rooms=[]
    human_shadow=load('shadow-human.png')
    for i,w in enumerate(cfg['rooms']):
        sprites=[load(f'room-{name}_{i}.png') for name in ('light','ghost','figure','curtain')]
        mask=load(f'room-mask_{i}.png')
        # Cache curtain movement frames and giant shadow fragments offline at startup.
        curtains=[]
        for dx in (-2,-1,0,1,2):
            s=pygame.Surface(w['size'],pygame.SRCALPHA); s.blit(sprites[3],(dx,0))
            s.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT); curtains.append(s)
        shadows=[]
        for frame in range(48 if i<4 else 0):
            s=pygame.Surface(w['size'],pygame.SRCALPHA)
            # One enormous coherent body moves behind the entire upper facade.
            x=185+frame*11-w['pos'][0]; y=175-w['pos'][1]
            s.blit(human_shadow,(x,y))
            s.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT); shadows.append(s)
        rooms.append((w,*sprites[:3],curtains,shadows))
    fog=load('fog.png')
    # Boost only texture alpha once at startup; keep per-frame rendering cheap.
    dense_fog=fog.copy()
    for yy in range(dense_fog.get_height()):
        for xx in range(dense_fog.get_width()):
            c=dense_fog.get_at((xx,yy)); c.a=min(255,round(c.a*2.5)); dense_fog.set_at((xx,yy),c)
    fog_layers=[(pygame.transform.smoothscale(dense_fog,(1100,150)),306,3,150),
                (pygame.transform.smoothscale(pygame.transform.flip(dense_fog,True,False),(960,120)),356,-5,195),
                (pygame.transform.smoothscale(dense_fog,(1000,95)),410,7,225)]
    bats=[load(f'bat_{i}.png') for i in range(3)]; bolt=load('lightning.png')
    doors=[load(f'door_{i}.png') for i in range(17)]; door_figure=load('door-figure.png')
    pumpkins=[load(f'pumpkin_{i}.png') for i in range(2)]
    candle_shades=[]
    for pic in pumpkins:
        shade=pygame.Surface(pic.get_size(),pygame.SRCALPHA); shade.fill((0,0,0,255))
        shade.blit(pic,(0,0),special_flags=pygame.BLEND_RGBA_MULT); shade.fill((0,0,0,0),special_flags=pygame.BLEND_RGB_MULT)
        candle_shades.append(shade)
    flash=pygame.Surface((800,480)); flash.fill((163,197,219))
    lamp=pygame.Surface((13,18),pygame.SRCALPHA); pygame.draw.ellipse(lamp,(255,167,63,150),(1,1,11,16))
    eyes=pygame.Surface((10,4),pygame.SRCALPHA)
    pygame.draw.circle(eyes,(145,171,123,130),(2,2),1); pygame.draw.circle(eyes,(145,171,123,130),(7,2),1)
    model=Timeline(a.seed,a.demo,startup_showtime=not(a.no_startup_showtime or a.demo or a.event))
    startup_pending=model.startup_showtime
    if a.event: model.haunt(a.event)
    clock=pygame.time.Clock(); running=True; frames=0; started=time.monotonic()
    def stop(*_):
        nonlocal running
        running=False
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    try:
        while running:
            dt=1/a.fps if a.fast_test else min(.25,clock.tick(a.fps)/1000)
            for e in pygame.event.get():
                if e.type in (pygame.WINDOWENTER,pygame.WINDOWFOCUSGAINED,pygame.MOUSEMOTION): pygame.mouse.set_visible(False)
                if e.type==pygame.QUIT: running=False
                elif e.type==pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE,pygame.K_q): running=False
                    elif e.key in (pygame.K_SPACE,pygame.K_h): model.haunt()
                    elif e.key==pygame.K_l: model.lightning()
                    elif e.key in (pygame.K_1,pygame.K_2,pygame.K_3): model.haunt(('windows','door','shadow')[e.key-pygame.K_1])
            model.update(dt,len(rooms)); t=model.now
            if startup_pending and not model.startup_showtime:
                print("MOONWAKE_STARTUP_SHOWTIME windows",flush=True)
                startup_pending=False
            if a.silhouette_room is not None: model.minor['silhouette']=(t-2,a.silhouette_room)
            screen.blit(bg,(0,0))
            # Moonlit exterior stays visible; only room/porch lamps follow house_light.
            for i,(w,light,ghost,figure,curtains,shadows) in enumerate(rooms):
                level=1 if a.all_lights else model.room_light(i)
                if model.strength('silhouette',i): level=max(level,.45)
                if model.event and model.event[0]=='shadow' and i<4: level=max(level,.8)
                light.set_alpha(round(level*255)); screen.blit(light,w['pos'])
                strength=model.ghost_strength(i)
                if strength:
                    ghost.set_alpha(round(strength*255)); screen.blit(ghost,w['pos'])
                if model.strength('silhouette',i): screen.blit(figure,w['pos'])
                if model.strength('curtain',i):
                    c=curtains[round(2+2*math.sin(model.strength('curtain',i)*math.pi*2))]
                    screen.blit(c,w['pos'])
                if model.event and model.event[0]=='shadow' and 2<=model.age<9 and i<4:
                    screen.blit(shadows[min(47,int((model.age-2)/7*48))],w['pos'])
                # Hidden figure exists only in the lightning-lit frame.
                if not a.no_flashes and model.flash>.05 and not model.event and i==model.flash_room:
                    ghost.set_alpha(240); screen.blit(ghost,w['pos'])
            opened=model.door_open
            if opened:
                n=max(1,round(opened*16)); screen.blit(doors[n],cfg['door'])
                if model.event and model.event[0]=='door' and 5<=model.age<10:
                    door_figure.set_alpha(round(min(1,(model.age-5)*2)*255)); screen.blit(door_figure,cfg['door'])
            lamp.set_alpha(round(model.porch_light*200)); screen.blit(lamp,(309,342)); screen.blit(lamp,(476,342))
            for i,pic in enumerate(pumpkins):
                # Restore the original pumpkin above the blackout mask, then dim its candle.
                screen.blit(pic,cfg['pumpkins'][i]); candle_shades[i].set_alpha(round((1-model.candles[i])*170))
                screen.blit(candle_shades[i],cfg['pumpkins'][i])
            eye_strength=model.strength('eyes')
            if eye_strength:
                eyes.set_alpha(round(eye_strength*170)); screen.blit(eyes,cfg['attic'])
            if 'bats' in model.minor:
                age=t-model.minor['bats'][0]
                for i in range(3):
                    screen.blit(bats[int(t*7+i)%3],(int(280-age*38+i*25),int(47+i*13+math.sin(t*2+i)*7)))
            for layer,y,speed,opacity in fog_layers:
                offset=int(t*speed)%layer.get_width(); layer.set_alpha(opacity)
                screen.blit(layer,(offset-layer.get_width(),y)); screen.blit(layer,(offset,y))
            if not a.no_flashes and model.flash>0:
                flash.set_alpha(round(model.flash*120)); screen.blit(flash,(0,0))
                bolt.set_alpha(round(model.flash*230)); screen.blit(bolt,(0,0))
            pygame.display.flip(); frames+=1
            if frames==1: print('MOONWAKE_READY v6 800x480',flush=True)
            if a.seconds>0 and t>=a.seconds: break
        if a.snapshot: pygame.image.save(screen,str(a.snapshot))
        print(json.dumps({'frames':frames,'scene_seconds':round(t,2),'wall_seconds':round(time.monotonic()-started,2),'events':model.counts}))
    finally: pygame.quit()
if __name__=='__main__': main()
