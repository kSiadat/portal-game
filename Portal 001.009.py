#================================================== Imports
from pygame import display, draw, event, FULLSCREEN, init, mouse, MOUSEBUTTONDOWN, MOUSEBUTTONUP, KEYDOWN, KEYUP, QUIT, Rect, time
from pygame import quit as pgQuit


#================================================== Functions
#=========================
def align(pos, altPos, portal, altPortal, dim):
    if (portal.dir[0]==0 and altPortal.dir[0]==0) or (portal.dir[1]==0 and altPortal.dir[1]==0):
        for x in range(2):
            if portal.pos[0][x] == portal.pos[1][x]:
                amountIn = abs(pos[x] + dim[x]*0.5*(portal.dir[x]+1) - portal.pos[0][x])
                proportionIn = amountIn / dim[x]
                altPos[x] = altPortal.pos[0][x] - altPortal.dir[x]*(amountIn - dim[x]*0.5*(1-altPortal.dir[x]))
            else:
                altPos[x] = altPortal.pos[0][x] - portal.pos[0][x] + pos[x]
    else:
        for x in range(2):
            if portal.pos[0][x] != portal.pos[1][x]:
                index = round(0.5 * (1 - portal.dir[1-x]*altPortal.dir[x]))
                offset = abs(pos[x] + dim[x]*index - portal.pos[index][x])
                altPos[1-x] = altPortal.pos[0][1-x] + offset
            else:
                proportionIn = abs(pos[x] + dim[x]*0.5*(portal.dir[x]+1) - portal.pos[0][x]) / dim[x]
                altPos[1-x] = altPortal.pos[0][1-x] - altPortal.dir[1-x]*(proportionIn*dim[1-x] - dim[x-1]*0.5*(1-altPortal.dir[1-x]))
    return altPos, proportionIn

#=========================
def check_collide(pos1, dim1, pos2, dim2):
    if pos2[0]<pos1[0]<pos2[0]+dim2[0] or pos2[0]<pos1[0]+dim1[0]<pos2[0]+dim2[0] or (pos1[0]<pos2[0] and pos2[0]+dim2[0]<pos1[0]+dim1[0]):
        if pos2[1]<pos1[1]<pos2[1]+dim2[1] or pos2[1]<pos1[1]+dim1[1]<pos2[1]+dim2[1] or (pos1[1]<pos2[1] and pos2[1]+dim2[1]<pos1[1]+dim1[1]):
            return True
    return False

#=========================
def check_cross(gradient, start, pos, dim, tag):
    def check(value, index, pos, dim):
        if pos[index] <= value <= pos[index]+dim[index]:
            return True
    cross = False
    retData = []
    for i in range(2):
        y = (gradient * (pos[0] + (i*dim[0]) - start[0])) + start[1]
        if check(y, 1, pos, dim):
            retData.append([pos[0]+(i*dim[0]), y, 1, tag])
    for i in range(2):
        x = ((pos[1] + (i*dim[1]) - start[1]) / gradient) + start[0]
        if check(x, 0, pos, dim):
            retData.append([x, pos[1]+(i*dim[1]), 0, tag])
    return retData

#=========================
def check_complete(goalPos, pos, dim):
    if goalPos[0][0]<=pos[0]<=pos[0]+dim[0]<=goalPos[1][0] and goalPos[0][1]<=pos[1]<=pos[1]+dim[1]<=goalPos[1][1]:
        return True
    return False

#=========================
def check_touch(pos1, dim1, pos2, dim2):
    if pos2[0]<=pos1[0]<=pos2[0]+dim2[0] or pos2[0]<=pos1[0]+dim1[0]<=pos2[0]+dim2[0] or (pos1[0]<=pos2[0] and pos2[0]+dim2[0]<=pos1[0]+dim1[0]):
        if pos2[1]<=pos1[1]<=pos2[1]+dim2[1] or pos2[1]<=pos1[1]+dim1[1]<=pos2[1]+dim2[1] or (pos1[1]<=pos2[1] and pos2[1]+dim2[1]<=pos1[1]+dim1[1]):
            return True
    return False

#=========================
def hyp(pos1, pos2):
    return (((pos1[0] - pos2[0])**2) + ((pos1[1] - pos2[1])**2)) **0.5

#=========================
def find_extreme(smallest, array):
    extreme = 0
    for a in range(len(array)):
        if smallest and array[a]<array[extreme]:
            extreme = a
        elif (not smallest) and array[a]>array[extreme]:
            extreme = a
    return extreme

#=========================
def inside(pos1, dim1, pos2_1, pos2_2, direction):
    if direction == 0:
        if (pos2_1[1]<pos1[1]<pos1[1]+dim1[1]<pos2_2[1] and pos1[0]<=pos2_1[0]<=pos1[0]+dim1[0]) or ((pos1[1]<=pos2_1[1]<pos1[1]+dim1[1] or pos1[1]<pos2_2[1]<=pos1[1]+dim1[1]) and pos1[0]<pos2_1[0]<pos1[0]+dim1[0]):
            return True
    else:
        if (pos2_1[0]<pos1[0]<pos1[0]+dim1[0]<pos2_2[0] and pos1[1]<=pos2_1[1]<=pos1[1]+dim1[1]) or ((pos1[0]<=pos2_1[0]<pos1[0]+dim1[0] or pos1[0]<pos2_2[0]<=pos1[0]+dim1[0]) and pos1[1]<pos2_1[1]<pos1[1]+dim1[1]):
            return True
    return False

#=========================
def new_portal(mP, mO, pos, tags=[-1,-1]):
    mO.add(portal(pos[:], mP.plats, tags))
    mP.delete(tags[0])
    for x in range(2):
        mP.add(platform(pos[x][:], [0,0], False, [False, tags[0]]))
    return mP, mO


#================================================== Class - character
class character():
    def __init__(self, initData):
        self.initData = initData
        self.colour = (50,50,50)
        self.m = 80#              mass
        self.dim = [0.5, 0.5]#    dimensions
        self.pos = initData[0][:]#   position
        self.posOld = self.pos[:]#position last frame
        self.f = [0, 0]#          force
        self.v = [0, 0]#          velocity
        self.a = [0, 0]#          acceleration
        self.g = -9.8 * self.m#   gravitational force
        self.grounded = False
        self.stunned = False
        self.jumps = [0, 0]
        self.jump = False
        self.moveForce = [800, 200]
        self.maxSpeed = [[5], [8, 50]]
        self.frictionMod = 1
        self.jumpForce = 30000
        self.inputs = [[119, 115, 97, 100], [32, 114]]
        self.pressed = [[False for x in range(4)], [False for x in range(3)]]
        self.inputM = [1, 3]
        self.clicked = [False, False]
        self.ignore = -1
        self.ignoreDir = [0, 0, 0]
        self.portal = 0
        self.alt = False
        self.altPos = self.pos[:]
        self.altPosOld = self.altPos[:]
        self.altIgnore = -1
        self.altIgnoreDir = [0, 0, 0]
        self.altPortal = 0
        self.altGrounded = False
        self.proportionIn = 0
        self.portalable = False
        self.portalPos = [[0,0], [0,0]]
        self.near = [0,0]
        self.portalSize = 2
        self.goalPos = initData[1][:]
        self.goalColour = (170,225,153)

#=========================
    def act(self):
        if self.grounded:
            if self.pressed[0][2] and not self.pressed[0][3]:
                self.f[0] -= self.moveForce[0]
                self.frictionMod = 1
            if self.pressed[0][3] and not self.pressed[0][2]:
                self.f[0] += self.moveForce[0]
                self.frictionMod = 1
        else:
            if self.pressed[0][2] and not self.pressed[0][3]:
                self.f[0] -= self.moveForce[1]
            if self.pressed[0][3] and not self.pressed[0][2]:
                self.f[0] += self.moveForce[1]
        if self.pressed[1][0]:
            if (not self.grounded) and self.jumps[1]<self.jumps[0]:
                self.jumps[1] += 1
                self.f[1] += self.jumpForce
                self.jump = True
            if self.grounded:
                self.f[1] += self.jumpForce
                self.jump = True
        if self.pressed[1][1]:
            self.__init__(self.initData)
            global mO
            mO.portals = [0, 0]

#=========================
    def aim(self, plats, portals):
        def place(near, bound, portalSize, i):
            portalPos = [[0,0], [0,0]]
            for j in range(2):
                portalPos[j][1-i] = near[1-i]
            if near[i] - bound[0] <= self.portalSize/2:
                portalPos[0][i] = bound[0]
                portalPos[1][i] = bound[0] + self.portalSize
            elif bound[1] - near[i] <= self.portalSize/2:
                portalPos[0][i] = bound[1] - self.portalSize
                portalPos[1][i] = bound[1]
            else:
                portalPos[0][i] = near[i] - self.portalSize/2
                portalPos[1][i] = near[i] + self.portalSize/2
            return portalPos
        self.portalable = False
        if not self.alt:
            centre = [self.pos[x]+self.dim[x]/2 for x in range(2)]
            valid = []
            values = []
            d = [(self.mPos[x] - centre[x]) for x in range(2)]
            for x in range(2):
                if d[x] == 0:
                    for P in plats:
                        if P.pos[x] <= centre[x] <= P.pos[x]+P.dim[x]:
                            if (self.mPos[1-x]>centre[1-x] and P.pos[1-x]>centre[1-x]) or (self.mPos[1-x]<centre[1-x] and P.pos[1-x]<centre[1-x]):
                                appendable = [0, 0, x, P.tag]
                                appendable[x] = centre[x]
                                if self.mPos[1-x]>centre[1-x] and P.pos[1-x]>centre[1-x]:
                                    appendable[1-x] = P.pos[1-x]
                                elif self.mPos[1-x]<centre[1-x] and P.pos[1-x]<centre[1-x]:
                                    appendable[1-x] = P.pos[1-x]+P.dim[1-x]
                                valid.append(appendable)
                                values.append(hyp(centre, appendable[:2]))
            if d[0]!=0 and d[1]!=0:
                gradient = d[1] / d[0]
                for P in plats:
                    checkMain = check_cross(gradient, centre, P.pos, P.dim, P.tag)
                    for check in checkMain:
                        if (self.mPos[0]>centre[0] and self.mPos[1]>centre[1] and check[0]>centre[0] and check[1]>centre[1]) or (self.mPos[0]>centre[0] and self.mPos[1]<centre[1] and check[0]>centre[0] and check[1]<centre[1]) or (self.mPos[0]<centre[0] and self.mPos[1]<centre[1] and check[0]<centre[0] and check[1]<centre[1]) or (self.mPos[0]<centre[0] and self.mPos[1]>centre[1] and check[0]<centre[0] and check[1]>centre[1]):
                            valid.append(check)
                            values.append(hyp(centre, check[:2]))
            if len(valid) > 0:
                near = valid[find_extreme(True, values)]
                self.near = near[:2]
                i = near[2]
                bound = [plats[near[3]].pos[i] + (j * plats[near[3]].dim[i]) for j in range(2)]
                if bound[1]-bound[0]>=self.portalSize:
                    self.portalPos = place(near, bound, self.portalSize, i)
                    positions = []
                    destroy = []
                    for P in portals:
                        if P!=0:
                            positions.append([P.pos, P.tag])
                    self.portalable = plats[near[3]].portalable
                    for P in positions:
                        if check_touch(self.portalPos[0], [self.portalPos[1][x]-self.portalPos[0][x] for x in range(2)], P[0][0], [P[0][1][x]-P[0][0][x] for x in range(2)]):
                            portals[P[1]] = 0
                            plats = [p for p in plats if p.pTag!=P[1]]

#=========================
    def calc_friction(self):
        ratio = (self.v[0] / self.maxSpeed[0][0])
        if self.grounded:
            friction = -self.moveForce[0] * ratio * self.frictionMod
            self.f[0] += friction
        if not (self.pressed[0][2] or self.pressed[0][3]):
            self.frictionMod = 2

#=========================
    def collide_platforms(self, fps, plats, pos, posOld, ignore, ignoreDir, portalEdge):
        def hit_side(side, v, pos, dim, pPos, pDim):
            for x in range(2):
                if side == x:
                    if v[x] <= 0:
                        pos[x] = pPos[x] + pDim[x]
                    else:
                        pos[x] = pPos[x] - dim[x]
            return pos
        v = [(pos[x]-posOld[x])*fps for x in range(2)]
        hit = False
        for P in plats:
            if P.tag!=ignore and ((not portalEdge) or (not P.original)):
                if ignore==-1 or (ignore!=-1 and not ((ignoreDir[0]==-1 and P.pos[0]+P.dim[0]<ignoreDir[2]) or (ignoreDir[0]==1 and ignoreDir[2]<P.pos[0]) or (ignoreDir[1]==-1 and P.pos[1]+P.dim[1]<ignoreDir[2]) or (ignoreDir[1]==1 and ignoreDir[2]<P.pos[1]))):
                    if check_collide(pos, self.dim, P.pos, P.dim):
                        hit = True
                        if P.pos[1]<posOld[1]<P.pos[1]+P.dim[1] or P.pos[1]<posOld[1]+self.dim[1]<P.pos[1]+P.dim[1] or (posOld[1]<P.pos[1]<=P.pos[1]+P.dim[1]<posOld[1]+self.dim[1]):
                            pos = hit_side(0, v, pos, self.dim, P.pos, P.dim)
                        elif P.pos[0]<posOld[0]<P.pos[0]+P.dim[0] or P.pos[0]<posOld[0]+self.dim[0]<P.pos[0]+P.dim[0] or (posOld[0]<P.pos[0]<=P.pos[0]+P.dim[0]<posOld[0]+self.dim[0]):
                            pos = hit_side(1, v, pos, self.dim, P.pos, P.dim)
                        else:
                            if abs(v[1])>abs(v[0]):
                                pos = hit_side(0, v, pos, self.dim, P.pos, P.dim)
                            else:
                                pos = hit_side(1, v, pos, self.dim, P.pos, P.dim)
        for P in plats:
            if pos[1]==P.pos[1]+P.dim[1] and v[1]<=0:
                self.grounded = True
                self.jumps[1] = 0
        return pos, hit

#=========================
    def collide_portals(self, portals):
        hit = False
        if portals[0]!=0 and portals[1]!=0:
            for P in portals:
                for x in range(2):
                    if P.pos[0][x] == P.pos[1][x]:
                        direction = x
                if inside(self.pos, self.dim, P.pos[0], P.pos[1], direction):
                    hit = True
                    self.alt = True
                    self.ignore = P.pTag
                    self.ignoreDir = P.dir[:]
                    self.portal = P.tag
                    self.altIgnore = portals[P.coTag].pTag
                    self.altIgnoreDir = portals[P.coTag].dir[:]
                    self.altPortal = P.coTag
                    self.altPos, self.proportionIn = align(self.pos, self.altPos, portals[self.portal], portals[self.altPortal], self.dim)
                    self.altPosOld, null = align(self.posOld, self.altPosOld, portals[self.portal], portals[self.altPortal], self.dim)
        if not hit:
            if self.alt:
                self.ignore = -1
                self.altIgnore = -1
                alting = False
                for x in range(2):
                    if (self.ignoreDir[x]==-1 and self.pos[x]+self.dim[x]<self.ignoreDir[2]) or (self.ignoreDir[x]==1 and self.ignoreDir[2]<self.pos[x]):
                        alting = True
                if alting:
                    self.altPos, self.proportionIn = align(self.pos, self.altPos, portals[self.portal], portals[self.altPortal], self.dim)
                    self.altPosOld, null = align(self.posOld, self.altPosOld, portals[self.portal], portals[self.altPortal], self.dim)
                    self.pos = self.altPos[:]
                    self.posOld = self.altPosOld[:]
            self.alt = False

#=========================
    def check_complete(self):
        if check_complete(self.goalPos, self.pos, self.dim):
            return True
        return False

#=========================
    def draw(self, scale, screenSize, portals):
        def cut(pos, dim, ignore, ignoreDir, limit):
            upper = [pos[x]+dim[x] for x in range(2)]
            lower = [pos[x] for x in range(2)]
            for x in range(2):
                if ignore!=-1 and ignoreDir[x]==1 and upper[x]>limit:
                    upper[x] = limit
                elif ignore!=-1and ignoreDir[x]==-1 and lower[x]<limit:
                    lower[x] = limit
            for x in range(2):
                diff = [upper[x]-lower[x] for x in range(2)]
            return lower, diff
        draw.rect(screen, self.goalColour, Rect(round(self.goalPos[0][0]*scale), round(screenSize[1]-(self.goalPos[0][1]*scale)), round((self.goalPos[1][0]-self.goalPos[0][0])*scale), round((self.goalPos[0][1]-self.goalPos[1][1])*scale)+1))
        if self.clicked[0] or self.clicked[1]:
            centre = [self.pos[x]+(self.dim[x]/2) for x in range(2)]
            if self.clicked[0]:
                colour = (0,102,204)
            else:
                colour = (225,85,0)
            draw.line(screen, colour, [round(centre[0]*scale), round(screenSize[1]-(centre[1]*scale))], [round(self.near[0]*scale), round(screenSize[1]-(self.near[1]*scale))], 2)
            self.portalable = False
        if portals[0]!=0 and portals[1]!=0:
            lower, diff = cut(self.pos, self.dim, self.ignore, self.ignoreDir, portals[self.portal].dir[2])
            draw.rect(screen, self.colour, Rect(round(lower[0]*scale), round(screenSize[1]-(lower[1]*scale)), round(diff[0]*scale), round(-diff[1]*scale)+1))
        else:
            draw.rect(screen, self.colour, Rect(round(self.pos[0]*scale), round(screenSize[1]-(self.pos[1]*scale)), round(self.dim[0]*scale), round(-self.dim[0]*scale)+1))
        if self.alt:
            lower, diff = cut(self.altPos, self.dim, self.altIgnore, self.altIgnoreDir, portals[self.altPortal].dir[2])
            draw.rect(screen, self.colour, Rect(round((lower[0]*scale)), round(screenSize[1]-(lower[1]*scale)), round(diff[0]*scale), round(-diff[1]*scale)+1))

#=========================
    def draw_aim(self, screenSize):
        if self.portalable:
            draw.line(screen, (255,0,0), [round(self.portalPos[0][0]*scale), round(screenSize[1]-(self.portalPos[0][1]*scale))], [round(self.portalPos[1][0]*scale), round(screenSize[1]-(self.portalPos[1][1]*scale))])

#=========================
    def gravity(self, portals):                    
        if self.alt:
            self.f[1] += self.g * (1 - self.proportionIn)
            if self.ignoreDir[1]!=0 and self.altIgnoreDir[1]!=0:
                self.f[1] -= self.g * self.proportionIn * self.ignoreDir[1] * self.altIgnoreDir[1]
            elif self.ignoreDir[0]!=0 and self.altIgnoreDir[0]!=0:
                self.f[1] += self.g * self.proportionIn
            else:
                self.f[0] += self.g * self.proportionIn * self.ignoreDir[1] * self.altIgnoreDir[1]
        else:
            self.f[1] += self.g

#=========================
    def input(self, keys, mouse, mPos, screenSize):
        self.mPos = mPos
        self.pressed[1] = [False for x in range(len(self.pressed[1]))]
        self.clicked = [False for x in range(2)]
        for K in keys:
            if K[0]:
                for i, I in enumerate(self.inputs):
                    for j, J in enumerate(I):
                        if J == K[1]:
                            self.pressed[i][j] = True
            elif not K[0]:
                for j, J in enumerate(self.inputs[0]):
                        if J == K[1]:
                            self.pressed[0][j] = False
        for M in mouse:
            if M[0]:
                for i, I in enumerate(self.inputM):
                    if I == M[1]:
                        self.clicked[i] = True

#=========================
    def move(self, fps, portals):
        for x in range(2):
            self.v[x] = (self.pos[x]-self.posOld[x]) * fps
        self.gravity(portals)
        self.calc_friction()
        if self.jump:
            self.v[1] = 0
            self.jump = False
        self.posOld = []
        for x in range(2):
            self.a[x] = self.f[x] / self.m
            self.v[x] += self.a[x] / fps
            self.posOld.append(self.pos[x])
            self.pos[x] += self.v[x] / fps
        self.f = [0, 0]
        self.reset()

#=========================
    def reset(self):
        if self.pos[1]<0:
            self.__init__(self.initData)


#================================================== Class - manager_character
class manager_character():
    def __init__(self):
        self.chars = []

    def act(self, screenSize):
        done = False
        keys = []
        click = []
        mPos = mouse.get_pos()
        mPos = [X for X in mPos]
        mPos[1] = screenSize[1] - mPos[1]
        for x in range(2):
            mPos[x] /= scale
        for E in event.get():
            if E.type == KEYDOWN:
                if E.key == 27:
                    done = True
                else:
                    keys.append([True, E.key])
            elif E.type == KEYUP:
                keys.append([False, E.key])
            elif E.type == MOUSEBUTTONDOWN:
                click.append([True, E.button])
            elif E.type == MOUSEBUTTONUP:
                click.append([False, E.button])
            elif E.type == QUIT:
                done = True
        for c in range(len(self.chars)):
            self.chars[c].input(keys, click, mPos, screenSize)
            self.chars[c].act()
        return done

#=========================
    def add(self, new):
        new.tag = len(self.chars)
        self.chars.append(new)

#=========================
    def aim(self, plats, portals):
        for c in range(len(self.chars)):
            self.chars[c].aim(plats, portals)

#=========================
    def collide_platforms(self, fps, plats, portals, portalEdge):
        for c in range(len(self.chars)):
            self.chars[c].grounded = False
            self.chars[c].pos, null = self.chars[c].collide_platforms(fps, plats, self.chars[c].pos, self.chars[c].posOld, self.chars[c].ignore, self.chars[c].ignoreDir, portalEdge)
            if self.chars[c].alt:
                self.chars[c].altPos, self.proportionIn = align(self.chars[c].pos, self.chars[c].altPos, portals[self.chars[c].portal], portals[self.chars[c].altPortal], self.chars[c].dim)
                self.chars[c].altPosOld, null = align(self.chars[c].posOld, self.chars[c].altPosOld, portals[self.chars[c].portal], portals[self.chars[c].altPortal], self.chars[c].dim)
                old = self.chars[c].altPos[:]
                self.chars[c].altPos, hit2 = self.chars[c].collide_platforms(fps, plats, self.chars[c].altPos, self.chars[c].altPosOld, self.chars[c].altIgnore, self.chars[c].altIgnoreDir, portalEdge)
                if hit2:
                    self.chars[c].pos, self.proportionIn = align(self.chars[c].altPos, self.chars[c].pos, portals[self.chars[c].altPortal], portals[self.chars[c].portal], self.chars[c].dim)
                    #self.chars[c].posOld, null = align(self.chars[c].altPosOld, self.chars[c].posOld, portals[self.chars[c].altPortal], portals[self.chars[c].portal], self.chars[c].dim)
                    #self.chars[c].proportionIn = 1 - self.chars[c].proportionIn

#=========================
    def collide_portals(self, portals):
        for c in range(len(self.chars)):
            self.chars[c].collide_portals(portals)

#=========================
    def check_complete(self):
        complete = False
        for c in range(len(self.chars)):
            complete = complete or self.chars[c].check_complete()
        return complete

#=========================
    def draw(self, scale, screenSize, portals):
        for c in range(len(self.chars)):
            self.chars[c].draw(scale, screenSize, portals)

#=========================
    def draw_aim(self, screenSize):
        for c in range(len(self.chars)):
            self.chars[c].draw_aim(screenSize)

#=========================
    def move(self, fps, portals):
        for c in range(len(self.chars)):
            self.chars[c].move(fps, portals)

#=========================
    def reset(self):
        for c in range(len(self.chars)):
            self.chars[c].reset()

#=========================
    def shoot(self, mP, mO):
        for c, C in enumerate(self.chars):
            for x in range(2):
                if C.clicked[x]:
                    self.chars[c].aim(mP.plats, mO.portals)
                    if self.chars[c].portalable:
                        mP, mO = new_portal(mP, mO, [[Y for Y in X] for X in C.portalPos[:]], [x, 1-x])
        return mP, mO


#================================================== Class - platform
class platform():
    def __init__(self, pos, dim, portalable, original=[True, -1]):
        self.pos = pos
        self.dim = dim
        self.portalable = portalable
        self.original = original[0]
        self.pTag = original[1]
        if self.portalable:
            self.colour = (200,200,200)
        else:
            self.colour = (100,100,100)

#=========================
    def draw(self, scale, screenSize):
        draw.rect(screen, self.colour, Rect(round(self.pos[0]*scale), round(screenSize[1]-(self.pos[1]*scale)), round(self.dim[0]*scale)+1, round(-self.dim[1]*scale)+1))


#================================================== Class - manager_platform
class manager_platform():
    def __init__(self):
        self.plats = []

#=========================
    def add(self, new):
        new.tag = len(self.plats)
        self.plats.append(new)

#=========================
    def delete(self, tag):
        self.plats = [P for P in self.plats if P.pTag!=tag]

#=========================
    def draw(self, scale, screenSize):
        for p in range(len(self.plats)):
            if self.plats[p].original:
                self.plats[p].draw(scale, screenSize)


#================================================== Class - portal
class portal():
    def __init__(self, pos, plats, tags):
        self.dir = [0, 0, 0]
        self.pos = pos
        self.tag = tags[0]
        self.coTag = tags[1]
        if self.tag == 0:
            self.colour = (0,102,204)
        elif self.tag == 1:
            self.colour = (225,85,0)
        for P in plats:
            for x in range(2):
                if pos[0][x] == pos[1][x]:
                    if pos[0][x]==P.pos[x] or pos[0][x]==P.pos[x]+P.dim[x]:
                        if P.pos[1-x]<=pos[0][1-x]<=P.pos[1-x]+P.dim[1-x] and P.pos[1-x]<=pos[1][1-x]<=P.pos[1-x]+P.dim[1-x]:
                            self.pTag = P.tag
                            if pos[0][x] == P.pos[x]:
                                self.dir[x] = 1
                            else:
                                self.dir[x] = -1
                            self.dir[2] = pos[0][x]

#=========================
    def draw(self, scale, screenSize):
        draw.line(screen, self.colour, [round(self.pos[0][0]*scale), round(screenSize[1]-(self.pos[0][1]*scale))], [round(self.pos[1][0]*scale), round(screenSize[1]-(self.pos[1][1]*scale))], 3)


#================================================== Class - manager_portal
class manager_portal():
    def __init__(self):
        self.portals = [0, 0]

#=========================
    def add(self, new):
        self.portals[new.tag] = new

#=========================
    def draw(self, scale, screenSize):
        for p in range(len(self.portals)):
            if self.portals[p]!=0:
                self.portals[p].draw(scale, screenSize)


#================================================== Levels
levels = []

levels.append([])
levels[-1].append([[5,5], [[24,4], [28,14]]])
levels[-1].append([[[ 4, 3], [24, 1], True],
                   [[ 4,14], [24, 1], True],
                   [[ 3, 4], [ 1,10], True],
                   [[28, 4], [ 1,10], True],
                   [[ 3, 3], [1,1], True],
                   [[ 3,14], [1,1], True],
                   [[28, 3], [1,1], True],
                   [[28,14], [1,1], True]])

levels.append([])
levels[-1].append([[5,6], [[24,6], [28,14]]])
levels[-1].append([[[ 4,5.4],[ 8,0.1], True],
                   [[20, 6], [ 8,0.1], True],
                   [[ 4, 4], [ 8,1.4],False],
                   [[20, 4], [ 8, 2], False],
                   [[ 4, 3], [24, 1], False],
                   [[ 4,14], [24, 1], False],
                   [[ 3, 4], [ 1,10], False],
                   [[28, 4], [ 1,10], False],
                   [[ 3, 3], [1,1], False],
                   [[ 3,14], [1,1], False],
                   [[28, 3], [1,1], False],
                   [[28,14], [1,1], False]])

levels.append([])
levels[-1].append([[5,12], [[25,11], [28,14]]])
levels[-1].append([[[12, 4],[ 8,0.1], True],
                   [[12,3.9],[8,0.1], False],
                   [[ 4, 4], [ 8, 7], False],
                   [[20, 4], [ 8, 7], False],
                   [[ 4, 3], [24, 1], False],
                   [[ 4,14], [24, 1], False],
                   [[ 3, 4], [ 1,10], False],
                   [[28, 4], [ 1,10], False],
                   [[ 3, 3], [1,1], False],
                   [[ 3,14], [1,1], False],
                   [[28, 3], [1,1], False],
                   [[28,14], [1,1], False]])

levels.append([])
levels[-1].append([[5,5], [[9,11], [12,14]]])
levels[-1].append([[[9,13.9],[12,0.1],False],
                   [[9,11],[0.1,3],False],
                   [[9,11],[3.1,0.1],False],
                   [[12,9],[0.1,2],False],
                   [[12,9],[5.1,0.1],False],
                   [[17,6.9],[0.1,2.1],False],
                   [[13,6.9],[4,0.1],False],
                   [[18.9,8],[0.1,3],False],
                   [[23.9,4],[0.1,2],False],
                   [[23.9,6],[4.1,0.1],False],
                   [[27.9,6],[0.1,8],False],
                   [[13,5],[0.1,2],False],
                   [[24,13.9],[4,0.1],False],
                   [[21,13.9],[1,0.1],True],
                   [[21,11.9],[ 1, 2],True],
                   [[22,13.9],[2,0.1],True],
                   [[ 8,5.7],[ 2,2.3],True],
                   [[ 8, 4], [ 2,1.3],True],
                   [[10, 3], [13.9,1],True],
                   [[23.9,3],[4.1,1], True],
                   [[ 4, 9], [ 5, 5], True],
                   [[ 9, 9], [ 3, 2], True],
                   [[ 4, 8], [ 4, 1], True],
                   [[ 8, 8], [ 2, 1], True],
                   [[10, 8], [ 2, 1], True],
                   [[12, 8], [ 1, 1], True],
                   [[12, 5], [ 1, 3], True],
                   [[13, 7], [ 4, 2], True],
                   [[19, 8], [ 5, 3], True],
                   [[24, 4], [ 4, 2], True],
                   [[ 4, 3], [ 4, 1], True],
                   [[ 8, 3], [ 2, 1], True],
                   [[ 4,14], [18, 1], True],
                   [[22,14], [ 2, 1], True],
                   [[24,14], [ 4, 1], True],
                   [[ 3, 4], [ 1, 4], True],
                   [[ 3, 8], [ 1, 6], True],
                   [[28, 4], [ 1,10], True],
                   [[ 3, 3], [1,1], True],
                   [[ 3,14], [1,1], True],
                   [[28, 3], [1,1], True],
                   [[28,14], [1,1], True]])


#================================================== Setup
fps = 60
init()
info = display.Info()

scale = info.current_w/32
screenSize = (info.current_w, info.current_h)
screen = display.set_mode(screenSize, FULLSCREEN)

'''
scale = 50
screenSize = (1600,900)
screen = display.set_mode(screenSize)
'''
clock = time.Clock()


#================================================== Mainloop
def mainLoop(mC, mP, mO, screen, display, clock, screenSize):
    done = mC.act(screenSize)
    mC.move(fps, mO.portals)
    mC.collide_platforms(fps, mP.plats, mO.portals, True)
    mC.collide_portals(mO.portals)
    mC.collide_platforms(fps, mP.plats, mO.portals, False)
    complete = mC.check_complete()
    mC.shoot(mP, mO)
    screen.fill((255,255,255))
    mC.draw(scale, screenSize, mO.portals)
    mP.draw(scale, screenSize)
    mO.draw(scale, screenSize)
    mC.draw_aim(screenSize)
    display.update()
    clock.tick(fps)
    return mC, mP, mO, done, complete

done = False
for level in levels:
    if not done:
        mC = manager_character()
        mP = manager_platform()
        mO = manager_portal()
        mC.add(character(level[0]))
        for plat in level[1]:
            mP.add(platform(plat[0], plat[1], plat[2]))
        complete = False
        while not (done or complete):
            mC, mP, mO, done, complete = mainLoop(mC, mP, mO, screen, display, clock, screenSize)
        if complete:
            for x in range(fps):
                mC, mP, mO, done, complete = mainLoop(mC, mP, mO, screen, display, clock, screenSize)

pgQuit()
