"""Seeded monotonic event scheduler, independent of rendering."""
import random
import math

class Timeline:
    durations = {'windows':19, 'door':16, 'shadow':14}
    intervals = {'ghost':(45,105), 'silhouette':(100,240), 'bats':(55,120), 'curtain':(80,170), 'eyes':(140,280), 'door_crack':(130,260)}
    lengths = {'ghost':12,'silhouette':14,'bats':9,'curtain':7,'eyes':5,'door_crack':12}
    def __init__(self, seed=None, demo=False, startup_showtime=False):
        self.rng=random.Random(seed); self.demo=demo; self.now=0.; self.event=None; self.previous=None
        self.flash_at=-100.; self.flash_room=0; self.minor={}; self.flickers={}; self.next_flickers={}
        self.candles=[.8,.7]; self.candle_due=[0,0]; self.rooms={}; self.room_due={}
        self.startup_showtime=bool(startup_showtime and not demo)
        self.next_haunt=15 if self.startup_showtime else 12 if demo else self.rng.uniform(180,360)
        self.next_flash=self.rng.uniform(65,150)
        self.due={k:self.rng.uniform(*v) for k,v in self.intervals.items()}
        self.counts={k:0 for k in ('windows','door','shadow','lightning',*self.intervals)}
    def lightning(self):
        self.flash_at=self.now; self.counts['lightning']+=1
    def haunt(self, kind=None):
        if self.event: return False
        if kind is None:
            choices=[k for k in self.durations if k!=self.previous]
            kind=choices[0] if self.demo else self.rng.choice(choices)
            if self.demo and self.previous: kind={'windows':'door','door':'shadow','shadow':'windows'}[self.previous]
        if kind not in self.durations: raise ValueError(kind)
        self.event=(kind,self.now); self.previous=kind; self.minor.clear(); self.counts[kind]+=1
        return True
    @property
    def age(self): return self.now-self.event[1] if self.event else 1000
    def update(self, dt, room_count, hand_count=0):
        self.now+=max(0,dt); t=self.now
        if self.event and self.age>=self.durations[self.event[0]]:
            self.event=None; self.next_haunt=t+(30 if self.demo else self.rng.uniform(180,360))
            self.due={k:t+self.rng.uniform(*v) for k,v in self.intervals.items()}
            self.next_flash=t+self.rng.uniform(65,150)
        if not self.event and t>=self.next_haunt:
            self.haunt("windows" if self.startup_showtime else None)
            self.startup_showtime=False
        if not self.event:
            self.minor={k:v for k,v in self.minor.items() if t-v[0]<self.lengths[k]}
            for k,due in self.due.items():
                if t>=due and (k=='bats' or not any(n!='bats' for n in self.minor)):
                    self.minor[k]=(t,self.rng.randrange(min(4,room_count)) if k=='silhouette' else self.rng.randrange(room_count)); self.counts[k]+=1
                    self.due[k]=t+self.rng.uniform(*self.intervals[k])
            if t>=self.next_flash:
                self.flash_room=self.rng.randrange(room_count); self.lightning(); self.next_flash=t+self.rng.uniform(65,150)
        for i in range(room_count):
            if i not in self.rooms:
                self.rooms[i]=i in (0,1,3,5); self.room_due[i]=t+self.rng.uniform(35,120)
            if t>=self.room_due[i] and not self.event:
                self.rooms[i]=not self.rooms[i]; self.room_due[i]=t+self.rng.uniform(35,120)
            if t>=self.next_flickers.get(i,0):
                self.flickers[i]=(t,self.rng.uniform(.15,.55),self.rng.uniform(.5,1.4))
                self.next_flickers[i]=t+self.rng.uniform(18,55)
        for i in range(2):
            if t>=self.candle_due[i]:
                self.candles[i]=self.rng.uniform(.45,1); self.candle_due[i]=t+self.rng.uniform(.09,.5)
    @property
    def flash(self):
        if self.event:
            starts={'windows':(.7,2.4,7.8),'door':(5,10),'shadow':(2,8)}[self.event[0]]
            return max(max(0,1-(self.age-s)/.22) if self.age>=s else 0 for s in starts)
        a=self.now-self.flash_at
        return max(0,1-a/.22) if a<.25 else max(0,.7-(a-.32)/.2) if a>=.32 else 0
    @property
    def house_light(self):
        if not self.event or self.event[0]!='windows': return 1
        if self.age<2.4: return max(0,1-self.age/2.4)
        return max(0,min(1,(self.age-10)/9))
    def room_light(self,i):
        level=.7 if self.rooms.get(i,i in (0,1,3,5)) else 0
        start,depth,duration=self.flickers.get(i,(-100,0,1)); a=self.now-start
        if 0<=a<duration: level*=1-depth*math.sin(a/duration*math.pi*3)**2
        return level*self.house_light
    def strength(self,kind,i=None):
        v=self.minor.get(kind)
        if not v or (i is not None and i!=v[1]): return 0
        a=self.now-v[0]
        return max(0,min(1,a/1.5,(self.lengths[kind]-a)/1.5))
    def ghost_strength(self,i):
        if self.event and self.event[0]=='windows' and 2.4<=self.age<7.8: return 1
        return self.strength('ghost',i)*.65
    @property
    def door_open(self):
        a=self.age if self.event and self.event[0]=='door' else self.now-self.minor['door_crack'][0] if 'door_crack' in self.minor else -1
        return max(0,min(1,(a-1)/3,(12-a)/3)) if a>=0 else 0
    @property
    def porch_light(self):
        if self.door_open or 'door_crack' in self.minor or self.event and self.event[0]=='door':
            return .2+.6*abs(math.sin(self.now*19)*math.sin(self.now*7))
        return self.house_light
