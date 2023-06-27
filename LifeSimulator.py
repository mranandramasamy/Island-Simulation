
import pygame, sys, time, random, math
from pygame.locals import *

WIDTH, HEIGHT = 1000, 600

class Vector:
    def __init__(self, x=0, y=0, randomize=False):
        self.x = x
        self.y = y
        if randomize:
            self.randomize()
    def ints(self):
        return (int(self.x), int(self.y))
    def randomize(self):
        self.x = random.randint(80, 880)
        self.y = random.randint(80, 560)

class Action:
    def __init__(self, action_set=None):
        self.avatar_index = 0
        if action_set is None:
            # ["MOVE", "TRY", "NEW_TARGET", "MATE"]
            self.action_type = random.choice(["MOVE"]*100+["TRY"]*10+["NEW_TARGET"]*60+["MATE"])
            self.move_direction = (random.choice([-1, 0, 1]), random.choice([-1, 0, 1])) if self.action_type=="NEW_TARGET" else None
            self.speed = random.randint(0, 3) if self.action_type=="NEW_TARGET" else None
            self.move_target_distance_percentage = random.randint(0, 100)/100 if self.action_type=="NEW_TARGET" else None
            self.in_the_vision = None
        else:
            # ["MOVE", "TRY", "NEW_TARGET", "MATE"]
            self.action_type = action_set[0]
            self.move_direction = action_set[1]
            self.speed = action_set[2]
            self.move_target_distance_percentage = action_set[3]
            self.in_the_vision = None
    def get_parse(self):
        return [ self.action_type, self.move_direction, self.speed, self.move_target_distance_percentage, self.in_the_vision ]

class Gene:
    def __init__(self, randomize=False):
        self.gender = "male"
        self.skin_color = (255, 255, 255)
        self.mating_interest = 0.5
        self.food_interest = 0.5
        self.vision = 15
        self.life_age_limit = 120
        if randomize:
            self.randomize()
    def randomize(self):
        self.gender = random.choice(["male", "female"])
        self.skin_color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
        self.mating_interest = random.randint(0, 100)/100
        self.food_interest = random.randint(0, 100)/100
        self.vision = random.choice([0]+[1]*20) * random.randint(15, 25) # will be blind 1 in 20 beings
        self.life_age_limit = random.randint(80, 150)

class Avatar:
    def __init__(self, x=WIDTH//2, y=HEIGHT//2):
        self.pos = Vector(x, y, randomize=True)
        self.speed = 2
        self.target = None
        self.energy = 6
        self.energy_life_zone = [1, 9]
        self.minimum_energy_for_mating = 5.5
        self.gene = Gene(randomize=True)
        self.size = 0.3
        self.grow_rate = 0.01
        self.goal_list = []
        self.move_direction = Vector(0, 0)
        self.current_goal = None
        self.cover_currounding_angles = 4
        self.is_dead = False
        self.dead_reason = None# ["NO FOOD", "OVER FOOD", "SEA"]
        self.landed_on = None
        self.age = 0
        self.age_rate = 0.01
        self.pregnancy_time = 3
        self.last_pregnant = 0
        self.is_pregnant = False
        self.baby = None
    def find_surroundings(self):
        angles = list(range(0, 360, 360//self.cover_currounding_angles))
        # print (self.gene.vision, angles)
        result = []
        for angle in angles:
            angle_rad = math.radians(angle)
            x = self.pos.x + self.gene.vision * math.cos(angle_rad)
            y = self.pos.y + self.gene.vision * math.sin(angle_rad)
            result.append((x, y))
        return result
    def set_pos(self, x=0, y=0):
        self.pos.x = x
        self.pos.y = y
    def add_goal(self, goal):
        self.goal_list.append(goal)
    def move(self):
        if (self.target is not None) and (self.target > 0):
            self.pos.x += (self.move_direction.x * min(self.speed, self.target))
            self.pos.y += (self.move_direction.y * min(self.speed, self.target))
            self.reduce_energy(0.0005)
    def set_direction(self, direction):
        self.move_direction.x = direction[0]
        self.move_direction.y = direction[1]
    def reduce_energy(self, rate=0.01):
        self.energy -= rate
        if self.energy<=self.energy_life_zone[0]:
            self.dead_reason = "NO FOOD"
            self.is_dead = True
            print ("dying due to no food")
    def add_energy(self, rate=0.01):
        self.energy += rate
        if self.energy_life_zone[1]<=self.energy:
            self.dead_reason = "OVER FOOD"
            self.is_dead = True
            print ("dying due to over food")
    def grow(self):
        self.size += self.grow_rate
    def on_goals(self):
        if len(self.goal_list)>0:
            self.current_goal = self.goal_list[0]
    def increase_age(self):
        self.age += self.age_rate
        if self.age >= self.gene.life_age_limit:
            print (f"dying due to age limit {self.gene.life_age_limit}")
            self.is_dead = True
    def __str__(self):
        return "Avatar pos:({}, {})  speed:{}, target:{}, energy:{}".format(self.pos.x, self.pos.y, self.speed, self.target, self.energy)

class Island:
    def __init__(self, initial_character_count=0):
        self.land_names = { "GRASS": (36, 80, 6), "GRASS2": (39, 95, 2), "GRASS3": (58, 109, 23), "SHORE": (189, 130, 70), "SEA3": (141, 153, 175), "SEA2": (123, 162, 233), "SEA1": (61, 128, 248), "SHIP": (102, 57, 49), "TREE": (21, 51, 0), "WATER": (12, 68, 168) }
        self.land_parts_by_color = { "36_80_6": "GRASS", "39_95_2": "GRASS2", "58_109_23": "GRASS3", "189_130_70": "SHORE", "141_153_175": "SEA3", "123_162_233": "SEA2", "61_128_248": "SEA1", "102_57_49": "SHIP", "21_51_0": "TREE", "12_68_168": "WATER" }
        self.avatars = []
        self.initial_character_count = initial_character_count
        self.initialize_avatars()
        self.alive_avatars_count = [len(self.avatars), len(self.avatars)]
    def initialize_avatars(self):
        self.avatars = []
        blind_avatars = 0
        for _ in range(self.initial_character_count):
            avatar = Avatar()
            self.avatars.append(avatar)
            if avatar.gene.vision == 0:
                blind_avatars += 1
        print (f"blind avatars count: {blind_avatars}")
    def mate(self, avatar_index, partner_avatar_index):
        baby = Avatar()
        new_gene = Gene()
        G1, G2 = self.avatars[avatar_index].gene, self.avatars[partner_avatar_index].gene
        new_gene.gender = random.choice([G1.gender, G2.gender])
        new_gene.skin_color = (
            (G1.skin_color[0]+G2.skin_color[0])//2,
            (G1.skin_color[1]+G2.skin_color[1])//2,
            (G1.skin_color[2]+G2.skin_color[2])//2
        )
        new_gene.mating_interest = (G1.mating_interest+G2.mating_interest)/2
        new_gene.food_interest = (G1.food_interest+G2.food_interest)/2
        new_gene.vision = (G1.vision+G2.vision)//2
        new_gene.life_age_limit = (G1.life_age_limit+G2.life_age_limit)//2 if random.choice([0, 1])==1 else random.randint(80, 150)
        baby.gene = new_gene
        if self.avatars[avatar_index].gene.gender == "female":
            self.avatars[avatar_index].is_pregnant = True
            self.avatars[avatar_index].baby = baby
            self.avatars[avatar_index].last_pregnant = self.avatars[avatar_index].age
            print (f"{avatar_index} got pregnant")
        elif self.avatars[partner_avatar_index].gene.gender == "female":
            self.avatars[partner_avatar_index].is_pregnant= True
            self.avatars[partner_avatar_index].baby = baby
            self.avatars[partner_avatar_index].last_pregnant = self.avatars[partner_avatar_index].age
            print (f"{partner_avatar_index} got pregnant")
        else:
            print (f"there is someting wrong with mating gender Avatar1: {self.avatars[avatar_index].gene.gender} & Avatar2: {self.avatars[partner_avatar_index].gene.gender} !!")
    def check_pregnancy(self, avatar_index):
        if self.avatars[avatar_index].is_pregnant:
            if (self.avatars[avatar_index].age - self.avatars[avatar_index].last_pregnant) >= (self.avatars[avatar_index].pregnancy_time):
                # delivers baby
                self.avatars[avatar_index].baby.pos.x = self.avatars[avatar_index].pos.x
                self.avatars[avatar_index].baby.pos.y = self.avatars[avatar_index].pos.y
                self.avatars.append(self.avatars[avatar_index].baby)
                self.avatars[avatar_index].is_pregnant = False
                self.alive_avatars_count[1] += 1
                print ("baby born :D")
    def act_on_avatar(self, avatar_index, action_set):
        self.check_pregnancy(avatar_index)
        if action_set.action_type == "MOVE":
            self.avatars[avatar_index].move()
        elif action_set.action_type == "NEW_TARGET":
            if self.avatars[avatar_index].gene.vision == 0:
                self.avatars[avatar_index].set_direction((0, 0))
                self.avatars[avatar_index].speed = 0
                self.avatars[avatar_index].target = 0
            else:
                self.avatars[avatar_index].set_direction(action_set.move_direction)
                self.avatars[avatar_index].speed = action_set.speed
                self.avatars[avatar_index].target = self.avatars[avatar_index].gene.vision * action_set.move_target_distance_percentage
        elif action_set.action_type == "TRY":
            # print (f"LAND: {self.avatars[avatar_index].landed_on}")
            if self.avatars[avatar_index].landed_on == "TREE":
                self.avatars[avatar_index].add_energy(0.02)
            elif self.avatars[avatar_index].landed_on == "WATER":
                self.avatars[avatar_index].add_energy(0.01)
            elif self.avatars[avatar_index].landed_on == "SEA1":
                self.avatars[avatar_index].is_dead = True
                print ("dying due to sea")
                self.avatars[avatar_index].dead_reason = "SEA"
            else:# GRASS, GRASS2, GRASS3, SHORE, SEA2, SEA3, SHIP
                pass
        elif action_set.action_type == "MATE":
            # print (action_set.in_the_vision)
            if "mating_partners" in action_set.in_the_vision:
                # print (f"""mating enabled: {action_set.in_the_vision["mating_partners"]}""")
                if len(action_set.in_the_vision["mating_partners"])>0:
                    partner_avatar_index = action_set.in_the_vision["mating_partners"][0]
                    self.mate(avatar_index, partner_avatar_index)
        if self.avatars[avatar_index].gene.vision == 0:
            self.avatars[avatar_index].reduce_energy(rate=0.001)
        self.avatars[avatar_index].increase_age()


class Simulator:
    def __init__(self, initial_character_count):
        self.play = True
        self.message = ""
        self.additional_message = ""
        self.island = Island(initial_character_count)
        self.current_land = None
        self.freeze_time = False
        self.dead_reasons = {}
        self.surface = None
        self.graphic_initialized = False
        self.background = None
        pygame.font.init()
        self.message_font = pygame.font.SysFont("Arial", 17)
        background = pygame.image.load("src/images/island-background.png")
        self.background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    def __init__for_render(self):
        self.graphic_initialized = True
        pygame.init()
        surface=pygame.display.set_mode((WIDTH, HEIGHT),0,32)
        self.fps=100
        self.ft=pygame.time.Clock()
        pygame.display.set_caption('The Simulation')
        self.surface=surface
        self.mouse=pygame.mouse.get_pos()
        self.click=pygame.mouse.get_pressed()
        self.color = {
            "background": (80, 141, 180),
            "male_avatar": (235, 35, 5),
            "female_avatar": (245, 0, 155),
            "male_avatar_dead": (245, 111, 91),
            "female_avatar_dead": (245, 103, 193),
            "land": (120, 60, 30),
            "avatar": (10, 30, 210),
            "surrounding_spot": (30, 240, 200)
        }
        self.graphic_initialized = True

    def set_message(self):
        # if len(self.island.avatars)>0:
        #     col = self.get_color(self.island.avatars[0].pos.ints())
        #     self.message = f"Avatars: {self.island.alive_avatars_count[0]}/{self.island.alive_avatars_count[1]} pos=({self.island.avatars[0].pos.ints()}) land={self.current_land} {self.additional_message}"
        # else:
        #     col = self.get_color(self.mouse)
        #     self.message = "pos=({}, {}) land={} {}".format(self.mouse[0], self.mouse[1], self.current_land, self.additional_message)
        col = self.get_color(self.mouse)
        self.message = f"Avatars: {self.island.alive_avatars_count[0]}/{self.island.alive_avatars_count[1]} pos=({self.mouse}) land={self.current_land} Age[0]: {round(self.island.avatars[0].age, 2)} {self.additional_message}"
    def get_color(self, pos):
        if 0<=pos[0]<WIDTH and 0<=pos[1]<HEIGHT:
            return self.background.get_at(pos)
        return (80, 141, 180) # some other color
    def get_avatar_position(self, avatar_index):
        mouse_position = self.island.avatars[avatar_index].pos.ints()
        return self.get_land_type(mouse_position)
    def get_color_code_with_pixel(self, color):
        if len(color) >= 3:
            return "{}_{}_{}".format(color[0], color[1], color[2])
        return None
    def get_land_type(self, pos):
        # print (f">> pos: {pos}")
        color_code = self.get_color_code_with_pixel(self.get_color(pos))
        # print (f">> color: {color_code}")
        if color_code is None:
            return None
        else:
            if color_code in self.island.land_parts_by_color:
                return self.island.land_parts_by_color[color_code]
            else:
                # print (f"color not found :D {color_code} at {pos}")
                return None
    def draw_message(self):
        text_surface = self.message_font.render(self.message, True, (0, 0, 0))
        self.surface.blit(text_surface, (5, 5))
    def draw_avatars(self):
        for avatar_index in range(len(self.island.avatars)):
            avatar = self.island.avatars[avatar_index]
            # print (f"gender: {avatar.gene.gender}")
            if avatar.is_dead:
                color = self.color["male_avatar_dead"] if avatar.gene.gender == "male" else self.color["female_avatar_dead"]
            else:
                color = self.color["male_avatar"] if avatar.gene.gender == "male" else self.color["female_avatar"]
            pygame.draw.circle(self.surface, color, avatar.pos.ints(), int(avatar.energy))
            if not avatar.is_dead:
                pygame.draw.circle(self.surface, self.color["surrounding_spot"], avatar.pos.ints(), avatar.gene.vision, 1)
                if avatar.is_pregnant:
                    pygame.draw.circle(self.surface, self.color["surrounding_spot"], avatar.pos.ints(), int(avatar.energy)+3, 1)
    def reset(self):
        self.island.initialize_avatars()
    def render(self):
        if not self.graphic_initialized:
            self.__init__for_render()
        self.surface.fill(self.color["background"])
        self.surface.blit(self.background, (0, 0))
        self.mouse=pygame.mouse.get_pos()
        self.click=pygame.mouse.get_pressed()
        #--------------------------------------------------------------
        self.draw_avatars()
        self.draw_message()
        self.handle_events()
        # -------------------------------------------------------------
        pygame.display.update()
        self.ft.tick(self.fps)
    def action(self, avatar_index, action_set):
        if not self.island.avatars[avatar_index].is_dead:
            self.act(avatar_index=avatar_index, randomize=False, action_set=action_set)
        else:
            dead_reason = self.island.avatars[avatar_index].dead_reason
            if dead_reason in self.dead_reasons:
                self.dead_reasons[dead_reason] += 1
            else:
                self.dead_reasons[dead_reason] = 1
        # print (energies)
    def get_distance(self, pos1, pos2):
        return math.sqrt(((pos1[0]-pos2[0])**2)+((pos1[1]-pos2[1])**2))
    def find_mating_partner_in_surrounding(self, avatar_index):
        avatars_can_mate = []
        if self.island.avatars[avatar_index].energy >= self.island.avatars[avatar_index].minimum_energy_for_mating:
            avatar_pos = self.island.avatars[avatar_index].pos.ints()
            distance_can_see = self.island.avatars[avatar_index].gene.vision
            gender = self.island.avatars[avatar_index].gene.gender
            for other_avatar_index in range(len(self.island.avatars)):
                if avatar_index!=other_avatar_index and gender!=self.island.avatars[other_avatar_index].gene.gender and (not self.island.avatars[other_avatar_index].is_pregnant):
                    other_pos = self.island.avatars[other_avatar_index].pos.ints()
                    if self.get_distance(avatar_pos, other_pos) <= distance_can_see:
                        if self.island.avatars[other_avatar_index].energy >= self.island.avatars[other_avatar_index].minimum_energy_for_mating:
                            avatars_can_mate.append(other_avatar_index)
        return avatars_can_mate[:]
    def identify_surrounds(self, avatar_index, list_of_surroundings_spots):
        in_the_vision = {
            "lands_covered": [],
            "mating_partners": []
        }
        for spot in list_of_surroundings_spots:
            in_the_vision["mating_partners"] = self.find_mating_partner_in_surrounding(avatar_index)
            in_the_vision["lands_covered"].append(self.get_land_type((int(spot[0]), int(spot[1]))))
        in_the_vision["lands_covered"] = list(set(in_the_vision["lands_covered"]))
        return in_the_vision
    def get_random_action_set(self, parse=False):
        action = Action()
        if parse:
            return action.get_parse()
        return action
    def act(self, avatar_index=0, randomize=True, action_set=None):
        if randomize or (action_set is None):
            action_set = self.get_random_action_set()
        landed_on = self.get_land_type(self.island.avatars[avatar_index].pos.ints())
        if landed_on is None:
            # print (self.island.avatars[avatar_index].pos.ints())
            self.island.avatars[avatar_index].is_dead = True
            # print ("dying due to no land")
            self.island.avatars[avatar_index].dead_reason = "OUT OF LAND"
        else:
            self.island.avatars[avatar_index].landed_on = landed_on
            # self.additional_message = action_set.action_type
            list_of_surroundings_spots = self.island.avatars[avatar_index].find_surroundings()
            in_the_vision = self.identify_surrounds(avatar_index, list_of_surroundings_spots)
            action_set.in_the_vision = in_the_vision
            self.island.act_on_avatar(avatar_index, action_set)
    def get_environment(self, avatar_index=0):
        avatar = self.island.avatars[avatar_index]
        list_of_surroundings_spots = avatar.find_surroundings()
        in_the_vision = self.identify_surrounds(avatar_index, list_of_surroundings_spots)
        return [
            avatar.pos.ints(), round(avatar.energy, 3), avatar.landed_on,
            in_the_vision["lands_covered"], in_the_vision["mating_partners"],
            avatar.is_pregnant, avatar.last_pregnant,
            avatar.is_dead
        ]
    def handle_events(self):
        for event in pygame.event.get():
            if event.type==QUIT:
                pygame.quit()
                sys.exit()
            if event.type==KEYDOWN:
                if event.key==K_SPACE:
                    self.freeze_time = not self.freeze_time
    def step(self, avatar_index, action_set):
        action = Action(action_set)
        self.action(avatar_index, action)
        return self.get_environment()

