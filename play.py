#!/usr/bin/python3
import pygame
#Can get this at https://github.com/Nearoo/pygame-text-input:
import pygame_textinput
import random
import math
from threading import Thread

#how many marbles?
MARBLES = 400
#how many pixels should an object move on each tick? #not currently used, theyre being set randomly.
ANIM_SPEED = 1
#limit frame rate to FPS with clock.tick(FPS) in your main loop.
FPS = 60
#how bigs your screen? go fullscreen on 'f' keypress. TODO: have pygame determine fullscreen size.
FULLSCREEN_DIM = (1366,768)
#prepend log statements with 'if VERBOSE == True:' and quickly toggle it on/off for debugging.
VERBOSE = False
#distance in px at which nodes can communicate current instruction to eachother:
BROADCAST_DISTANCE = 10

clock = pygame.time.Clock()
pygame.init()

def init_display(WIDTH,HEIGHT):
    global screen,background
    SIZE = WIDTH, HEIGHT
    if WIDTH <= 800:
        screen = pygame.display.set_mode(SIZE)
    if WIDTH > 800:
        screen = pygame.display.set_mode(SIZE, pygame.FULLSCREEN)
    background = screen.copy()
    background.fill((0, 0, 0, 0))
    screen.blit(background, (0, 0))

init_display(800,600)



boom = pygame.image.load('marbles/boom.png')
boom.set_colorkey((0,0,0))
boom.set_alpha(110)


#get 'close enough' to target. returns how close we are in px.
def calc_distance(c1,c2):
    test = max( (abs(c1[0] - c2[0])), (abs(c1[1] - c2[1])) )
    return(test)

class SimpleObject: #totally change me
    register = list()
    def __init__(self, title, image, target, position, radius, angle, phase, current_instruction=[], speed=ANIM_SPEED, antenna = None, boom=0):
        self.__class__.register.append(self)
        self.title    = title
        self.image    = image
        self.target   = image.get_rect().move(*target)
        self.position = image.get_rect().move(*position)
        self.radius   = radius
        self.angle    = angle
        self.phase    = phase
        self.current_instruction = current_instruction
        self.speed    = speed
        self.antenna  = None
        self.boom     = boom
        self.bpoints  = [(0,0)]

    def update(self,tick=1):
        tick = 0
        if calc_distance(
          (self.position.x,self.position.y),
          (self.target.x,self.target.y)   ) <= 10+ANIM_SPEED:
                self.position.x = self.target.x
                self.position.y = self.target.y
                return True

        if self.position.centery > self.target.y:
            self.position.centery -= 1 * ANIM_SPEED
        if self.position.centerx > self.target.x:
            self.position.centerx -= 1 * ANIM_SPEED
        if self.position.centery < self.target.y:
            self.position.centery += 1 * ANIM_SPEED
        if self.position.centerx < self.target.x:
            self.position.centerx += 1 * ANIM_SPEED
        return False

    def receive(self):
            for i in SimpleObject.register:
                #print("i:{} self:{}".format(i.current_instruction, self.current_instruction))
                if calc_distance(\
                    (self.position.x,self.position.y),(i.position.x, i.position.y))  <= BROADCAST_DISTANCE:
                        if i.current_instruction[1] > self.current_instruction[1]: #if the instruction is newer than ours:
                            self.current_instruction = i.current_instruction
                            self.boom = 1
                            self.antenna = i

    #second part of animation cycle. see below in main loop.
    def draw(self, screen):
        if self.boom is not 0 and self.boom < FPS/4:
            screen.blit(boom,(self.position.centerx,self.position.centery))
            self.boom+=1
        else:
            self.boom = 0
            screen.blit(self.image, self.position)
        if self.antenna is not None:
            color = [20,20,220]
            if self.current_instruction[0] == 'whirlwind':
                color = [200,20,220]
            if self.current_instruction[0] == 'spiral':
                color = [200,40,110]
            if self.current_instruction[0] == 'rando':
                color = [60,60,200]
            if self.current_instruction[0] == 'orbit':
                color = [80,200,80]
            if self.current_instruction[0] == 'cluster':
                color = [244,244,244]
            pygame.draw.line(screen , color, (self.antenna.position.centerx,self.antenna.position.centery), (self.position.centerx,self.position.centery), 1)




class Hub:
    def __init__(self,title,image,stats={},mm_position=[]):
        self.title                  = title
        self.image                  = image
        self.stats                  = stats
        self.mm_position            = mm_position

    def update(self):
        self.stats['random_carry'],self.stats['orbit_carry'],self.stats['spiral_carry'],self.stats['whirlwind_carry'] = 0,0,0,0
        for i in SimpleObject.register:
            if i.current_instruction[0] == 'rando':
                self.stats['random_carry']+=1
            if i.current_instruction[0] == 'spiral':
                self.stats['spiral_carry']+=1
            if i.current_instruction[0] == 'orbit':
                self.stats['orbit_carry']+=1
            if i.current_instruction[0] == 'whirlwind':
                self.stats['whirlwind_carry']+=1

        #self.mm_position = [master_marble.position.x,master_marble.position.y]

    def draw(self, screen):
        color=(106, 90, 240, 0)
        font = pygame.font.SysFont("Arial", 16) #30 is size
        build_phrase = \
        "Orbit carry: {} count: {} | Spiral carry: {} count: {} | Random carry: {} count: {} | Whirlwind carry: {} count {}".format(\
        self.stats["orbit_carry"],\
        self.stats["orbit_packets"],\
        self.stats["spiral_carry"],\
        self.stats["spiral_packets"],\
        self.stats["random_carry"],\
        self.stats["random_packets"],\
        self.stats["whirlwind_carry"],\
        self.stats["whirlwind_packets"],\
        )
        self.image = font.render(build_phrase, True, color)
        screen.blit(self.image, (40,screen.get_height()-40) )
        #for k,v in zip(self.__dict__.keys(),self.__dict__.values()):
        #        print ("{}: {}".format(k,v))


#make an onscreen prompt to take text entry. returns phrase entered.
#uses pygame_textinput from
#https://raw.githubusercontent.com/Nearoo/pygame-text-input/master/pygame_textinput.py
def input(location=[10,10],prompt=None,size=30):
    color=(106, 90, 205, 0)
    if prompt is not None:
        font = pygame.font.SysFont("Arial", size)
        prompt_surface = font.render(prompt, True, color)
        prompt_location = location
        location=[prompt_surface.get_rect().width+20,location[1]]
    textinput = pygame_textinput.TextInput(
                font_family="Arial",
                font_size = size,
                text_color=color,
                antialias=True              )
    events = ""
    while textinput.update(events) == False: #returns true at Enter key
        events = pygame.event.get()
        if prompt_surface:
            screen.blit(prompt_surface,prompt_location)
        screen.blit(textinput.get_surface(),location)
        pygame.display.update()
        clock.tick(FPS)
    return(textinput.get_text())

def render_hub(hub):
    color=(106, 90, 96, 0)
    font = pygame.font.SysFont("Arial", 12) #30 is size
    build_phrase = "Orbit carry: {} count: {} | Spiral carry: {} count: {} | \
Random carry: {} count: {}".format(hub.stats["orbit_carry"],hub.stats["orbit_packets"],\
hub.stats["spiral_carry"],hub.stats["spiral_packets"],hub.stats["random_carry"],hub.stats["random_packets"],\
hub.stats["whirlwind_carry"],hub.stats["whirlwind_packets"])
    surface = font.render(build_phrase, True, color)
    print('surface '+str(surface))
    return surface


#load a marble  #################################################################################### marble init
def marble(name):
    marble = pygame.image.load('marbles/redbig2.png')
    middle_of_display = ( screen.get_width()/2, screen.get_height()/2 )
    x,y = random.randint(10,screen.get_width()),random.randint(10,screen.get_height())
    mob = SimpleObject(
            title = name,
            image = marble,
            target = (x+random.random(),y+random.random()),
            position = (x,y),
            radius = random.randint(20,screen.get_height()/2),
            angle = random.randint(1,360),
            phase = True,
            current_instruction = [0,0],
            speed = random.randint(0,6),
                            )
    return mob

def do_comms(batch):
        while True:
            #print("COMMS: "+str(len(SimpleObject.register)))
            # COMMUNICATE BETWEEN NODES
            for x in batch:
                x.receive()

def load_exit_sign():
    exit_sign = pygame.image.load('marbles/exit.png')
    exit_sign = pygame.transform.smoothscale(exit_sign,(60,30))
    background.blit(exit_sign,exit_sign.get_rect().move(0,0))

#"The Circle Equation"
#change angle 0-360 to have any (x,y) on circumference
Pi= 3.14159265358979323846
def poc(radius,angle,origin):
    x = (radius * math.cos(angle * Pi/180) ) + origin[0]
    y = (radius * math.sin(angle * Pi/180) ) + origin[1]
    return x,y

#Expects: [(x,y),(x,y),(x,y),(x,y)]. returns same (a list of x,y tuples.)
#this is used by the 'bezier flower' pattern below.
def compute_bezier_points(vertices, numPoints=None):
    if numPoints is None:
        numPoints = 30
    if numPoints < 2 or len(vertices) != 4:
        return None
    result = []
    b0x = vertices[0][0]
    b0y = vertices[0][1]
    b1x = vertices[1][0]
    b1y = vertices[1][1]
    b2x = vertices[2][0]
    b2y = vertices[2][1]
    b3x = vertices[3][0]
    b3y = vertices[3][1]
    # Compute polynomial coefficients from Bezier points
    ax = -b0x + 3 * b1x + -3 * b2x + b3x
    ay = -b0y + 3 * b1y + -3 * b2y + b3y
    bx = 3 * b0x + -6 * b1x + 3 * b2x
    by = 3 * b0y + -6 * b1y + 3 * b2y
    cx = -3 * b0x + 3 * b1x
    cy = -3 * b0y + 3 * b1y
    dx = b0x
    dy = b0y
    # Set up the number of steps and step size
    numSteps = numPoints - 1 # arbitrary choice
    h = 1.0 / numSteps # compute our step size
    # Compute forward differences from Bezier points and "h"
    pointX = dx
    pointY = dy
    firstFDX = ax * (h * h * h) + bx * (h * h) + cx * h
    firstFDY = ay * (h * h * h) + by * (h * h) + cy * h
    secondFDX = 6 * ax * (h * h * h) + 2 * bx * (h * h)
    secondFDY = 6 * ay * (h * h * h) + 2 * by * (h * h)
    thirdFDX = 6 * ax * (h * h * h)
    thirdFDY = 6 * ay * (h * h * h)
    # Compute points at each step
    result.append((int(pointX), int(pointY)))
    for i in range(numSteps):
        pointX += firstFDX
        pointY += firstFDY
        firstFDX += secondFDX
        firstFDY += secondFDY
        secondFDX += thirdFDX
        secondFDY += thirdFDY
        result.append((int(pointX), int(pointY)))
    return result


#bezier flower:
def bezier_flower():
    middle = (screen.get_width()/2,screen.get_height()/2)
    wext,hext = middle[0]*2,middle[1]*2
    c1=[(middle),(-100,-100),(wext+200,-200),(middle)] #top
    c2=[(middle),(-100,hext+100),(wext+100,hext+100),(middle)]

    c3=[(middle),(wext+100,-100),(wext+100,hext+100),(middle)]
    c4=[(middle),(-100,hext+100),(-100,-100),(middle)]

    all_points = []
    for coordinates in [c1,c2,c3,c4]:
        all_points.append(compute_bezier_points( [ (x[0], x[1]) for x in coordinates ] ) ) 
    lm=[i for sublist in all_points for i in sublist]
    print(lm)
    return(lm)



#a 'generator' for any list, since python 'generators' cant seem to be troubled to do anything like this.
def lnext(alist,x,y,ticker):
    try:
        val = alist[ticker]
        ticker+=1
    except:
        ticker = 0
        val = alist[0]
    return(val[0],val[1],ticker)

#produce a handful of rando lists to distribute amongst the marbs.
def bezier_monster(master_marble):
    b_points = []
    control_points = [\
( random.randint(0,screen.get_height()+200 ),random.randint(0,screen.get_width()+400 ) ),\
(random.randint(0,screen.get_width()+200 ),random.randint(0,screen.get_width()+400) ),\
(random.randint(0,screen.get_width() ),random.randint(0,screen.get_width()+400) ),\
(random.randint(0,screen.get_width() ),random.randint(0,screen.get_width() )) ]

    bpoints = compute_bezier_points( [ (x[0],x[1]) for x in control_points ] )
    return(bpoints)

#main. some setup, then enter draw/update/check for input endless loop.
def main():
    global ANIM_SPEED,MARBLES,FPS
    tick=clock.tick(FPS)  # Limit the framerate to FPS
    anim_status = []

    load_exit_sign()

    hub = Hub('hub',image=None,
          stats = {'orbit_packets':0,\
          'orbit_carry':0,'random_packets':0,\
          'random_carry':0,'spiral_packets':0,'spiral_carry':0,\
          'whirlwind_packets':0,'whirlwind_carry':0}
          )
    hub.image = render_hub(hub)


    #make maaad marbles. but in batches.
    if MARBLES < 5: exit()
    for h in range(int(MARBLES/5)):
        for i in range(5):
            marble('marble_'+str(i+(h*h)) )
        # DRAW GAME OBJECTS
        screen.blit(background, (0, 0))  # Fill entire screen.
        for x in SimpleObject.register:
                x.draw(screen)
        # UPDATE GAME OBJECTS
        for x in SimpleObject.register:
            anim_status.append(x.update(tick))
        pygame.display.update()

    print("{} marbles added!".format(len(SimpleObject.register)) )
    master_marble = SimpleObject.register[0] #until otherwise chosen by any click.

    #batch out the comms job to own thread:
    comms = Thread(target = do_comms,args=[SimpleObject.register])
    comms.daemon=True
    comms.start()

    if VERBOSE == True:
        for i in SimpleObject.register:
            for k,v in zip(i.__dict__.keys(),i.__dict__.values()):
                print ("{}: {}".format(k,v) )
            print("position: {},{}".format(i.position.x,i.position.y))
            print("target: {},{}".format(i.target.x,i.target.y))
            print("-------------------------")


#### Main update/draw/listen loop ####
    running = True
    while running:
        tick = clock.tick(FPS)
        ########################## transforms ######################################
        #for each marble, if marble has arrived at last dest:
        for i in SimpleObject.register:
            if i.position.x == i.target.x and i.position.y == i.target.y:
                if i.current_instruction[0] == 'orbit':
                    #rotate around  on our circles circumference. toggled on and off by key "S" (for 'spin')
                    middle_of_display = ( screen.get_width()/2-20, screen.get_height()/2-60 )
                    if i.angle < 360:
                        i.angle+=i.speed
                    else: i.angle = 0
                    i.target.x,i.target.y = poc(i.radius,i.angle,middle_of_display)

                if i.current_instruction[0] == 'rando':
                    i.target.x = random.randint(0,screen.get_width())
                    i.target.y = random.randint(0,screen.get_height())

                if i.current_instruction[0] == 'spiral':
                    middle_of_display = ( screen.get_width()/2-20, screen.get_height()/2-60 )
                    if i.angle < 360:
                            i.angle+=i.speed
                    else: i.angle = 0
                    if i.radius < screen.get_width()/2:
                            i.radius+=3
                    else: i.radius = 1
                    i.target.x,i.target.y = poc(i.radius,i.angle,middle_of_display)

                if i.current_instruction[0] == 'whirlwind':
                    i.target.x,i.target.y,i.phase = lnext(b_points,i.position.x,i.position.y,i.phase)                    #print(master_marble.bpoints)

                if i.current_instruction[0] == 'cluster':
                    try: cluster_coords
                    except: cluster_coords = [350,350]
                    i.target.x,i.target.y = \
                        random.randint(cluster_coords[0]-70,cluster_coords[0]+70),\
                        random.randint(cluster_coords[1]-70,cluster_coords[1]+70)

        if VERBOSE == 'MEGA':
            for i in SimpleObject.register:
                print(i)
                for k,v in zip(i.__dict__.keys(),i.__dict__.values()):
                    print ("{}: {}".format(k,v) )
                print("position: {},{}".format(i.position.x,i.position.y))
                print("target: {},{}".format(i.target.x,i.target.y))
                print("-------------------------")

        # HANDLE EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            #mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                cx,cy = pygame.mouse.get_pos()
                print("clicked {},{}".format(cx,cy))
                if (cx < 60) and (cy < 30):
                    print("clicked exit sign")
                    running = False
                for i in SimpleObject.register:
                    if i.position.collidepoint(cx,cy) == True:
                        print("New Master: {}".format(i.title) )
                        master_marble = i #now user can change who receives init instructions!
                cluster_coords = [cx,cy]
            #keyboard keys
            if event.type == pygame.KEYDOWN:
                try: event.key
                except: event.key="0"
                if event.key == pygame.K_DOWN: #speed down
                    if ANIM_SPEED > 1:
                        ANIM_SPEED-=1
                        print("speed "+str(ANIM_SPEED))
                    else: print("min speed reached")
                if event.key == pygame.K_UP: #speed up
                    ANIM_SPEED+=1
                    print("speed "+str(ANIM_SPEED))
                if event.key == pygame.K_o: #'orbit'
                    master_marble.current_instruction = ['orbit',pygame.time.get_ticks()]
                    print(str(master_marble.current_instruction))
                    hub.stats['orbit_packets']+=1
                if event.key == pygame.K_s: #'spiral'
                    master_marble.current_instruction = ['spiral',pygame.time.get_ticks()]
                    print(str(master_marble.current_instruction))
                    hub.stats['spiral_packets']+=1
                if event.key == pygame.K_w: #'whirlwind'
                    master_marble.current_instruction = ['whirlwind',pygame.time.get_ticks()]
                    b_points = bezier_flower()
                    print(str(master_marble.current_instruction))
                    hub.stats['whirlwind_packets']+=1
                if event.key == pygame.K_r: #'random'
                    master_marble.current_instruction = ['rando',pygame.time.get_ticks()]
                    print(str(master_marble.current_instruction))
                    hub.stats['random_packets']+=1
                if event.key == pygame.K_c: #'cluster'
                    master_marble.current_instruction = ['cluster',pygame.time.get_ticks()]
                    print(str(master_marble.current_instruction))
                    #hub.stats['cluster_packets']+=1
                if event.key == pygame.K_SPACE:
                    try: paused, prev_speed
                    except: paused,prev_speed = False, []
                    paused = not paused
                    print("paused: {}, {}".format(paused,prev_speed))
                    if paused == True:
                        prev_speed = [ANIM_SPEED,FPS]
                        FPS = 0
                        ANIM_SPEED = 0
                    if paused == False:
                        FPS=prev_speed[1]
                        ANIM_SPEED=prev_speed[0]

                if event.key == pygame.K_q: #Q - quit
                    print("Quitting due to 'q' press")
                    pygame.quit()
                if event.key == pygame.K_t: #N - enter text
                        new_entry = input(prompt='your prompt:')
                        print("user entered: {}".format(new_entry) )
                if event.key == pygame.K_UP:
                        print("FPS limit {}".format(FPS) )
                        FPS+=10
                        print("px per draw {}".format(ANIM_SPEED) )
                        ANIM_SPEED+=2
                if event.key == pygame.K_DOWN:
                        if FPS >= 10:
                            FPS-=10
                        else: FPS=1
                        print("speed {}".format(FPS) )
                        if ANIM_SPEED >= 2:
                            ANIM_SPEED-=2
                        else: ANIM_SPEED=2
                        print("px per draw {}".format(ANIM_SPEED) )
                if event.key == pygame.K_f: #F - full screen
                    if screen.get_width() > 800:
                        init_display(800,600)
                        pygame.event.set_grab(False)
                        break
                    if screen.get_width() == 800:
                        pygame.event.set_grab(True)
                        init_display(*FULLSCREEN_DIM)
                        load_exit_sign()

        # DRAW GAME OBJECTS
        screen.blit(background, (0, 0))  # Fill entire screen.
        for x in SimpleObject.register:
                x.draw(screen)
        hub.draw(screen)
        # UPDATE GAME OBJECTS
        for x in SimpleObject.register:
            anim_status.append(x.update(tick))
        hub.update()
        pygame.display.update()



if __name__ == '__main__':
    main()
