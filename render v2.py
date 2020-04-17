import cv2
import numpy as np
import random
import datetime as dt
import math
from tqdm import tqdm
import cProfile, pstats, io

height = 400
width = 400

image = np.full((height, width, 3), 50, np.uint8)


def draw_room():
    # no max width or height values (eg. 400->399)

    # walls
    walls_lines = []
    walls = [[[160, 110], [190, 110], [190, 140], [160, 140]],
             [[260, 210], [290, 210], [290, 240], [260, 240]],
             [[90, 270], [130, 270], [130, 310], [90, 310]]]

    for i in range(0, len(walls)):
        cv2.fillPoly(image, pts=[np.array(walls[i])], color=(0, 0, 0))

        for j in range(0, len(walls[i])):
            if j != len(walls[i]) - 1:
                walls_lines.append([walls[i][j], walls[i][j + 1]])
            else:
                walls_lines.append([walls[i][j], walls[i][0]])

    # lights
    lights_lines = []
    lights = [[[250, 80], [300, 80], [320, 100], [320, 150], [300, 170], [250, 170], [230, 150], [230, 100]],
              [[160, 210], [180, 210], [190, 220], [190, 240], [180, 250], [160, 250], [150, 240], [150, 220]]]

    for i in range(0, len(lights)):
        cv2.fillPoly(image, pts=[np.array(lights[i])], color=(255, 255, 255))

        for j in range(0, len(lights[i])):
            if j != len(lights[i]) - 1:
                lights_lines.append([lights[i][j], lights[i][j + 1]])
            else:
                lights_lines.append([lights[i][j], lights[i][0]])

    return walls_lines, walls, lights_lines, lights


def intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    q1, q2, q3, q4 = (x1 - x2), (y3 - y4), (y1 - y2), (x3 - x4)
    d = q1 * q2 - q3 * q4

    if not d:
        return None

    q5, q6 = (x1 - x3), (y1 - y3)
    t2 = -(q1 * q6 - q3 * q5) / d

    if t2 > 0:
        n = q5 * q2 - q6 * q4
        t1 = n / d

        if 0 < t1 < 1:
            return int(x1 + t1 * (x2 - x1)), int(y1 + t1 * (y2 - y1))


def define_areas(x, y):
    def get_relative_angle(v1, v2):
        f1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        f2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

        uv1 = [v1[0] / f1, v1[1] / f1]
        uv2 = [v2[0] / f2, v2[1] / f2]

        dot_product = np.dot(uv1, uv2)
        product = math.degrees(np.arccos(dot_product))

        if math.isnan(product):
            angle = 0
        else:
            angle = int(math.degrees(np.arccos(dot_product)))

        return angle

    def get_angle(v1, v2):
        f1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        f2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

        uv1 = [v1[0] / f1, v1[1] / f1]
        uv2 = [v2[0] / f2, v2[1] / f2]

        dot_product = np.dot(uv1, uv2)

        angle = int(math.degrees(np.arccos(dot_product)))

        if uv2[0] < uv1[0]:
            angle = -angle

        return angle

    def generate_degrees(areas):
        degrees = set([])

        for area in areas:
            if area[0] > area[1]:
                for i in range(area[0], 360):
                    degrees.add(i)
                for i in range(0, area[1] + 1):
                    degrees.add(i)
            else:
                for i in range(area[0], area[1] + 1):
                    degrees.add(i)
        return degrees

    areas = []
    for object in lights_points:
        values = []
        angles = []
        value = 0

        v1 = np.array([object[0][0] - x, object[0][1] - y])

        for point in object:
            v2 = np.array([point[0] - x, point[1] - y])

            angle_1 = get_angle([0, -1], v2)
            if v1[0] != v2[0] or v1[1] != v2[1]:
                angle_2 = get_angle([0, -1], v1)

                if angle_1 > angle_2:
                    # left
                    ang = get_relative_angle(v1, v2)
                else:
                    # right
                    ang = -get_relative_angle(v1, v2)
                if abs(angle_1 - angle_2) > 180:
                    # Changing sides
                    ang = -ang
                value += ang

            v1 = np.array([point[0] - x, point[1] - y])

            if angle_1 < 0:
                angle_1 += 360

            angles.append(angle_1)
            values.append(value)

        areas.append([angles[np.argmin(values)], angles[np.argmax(values)]])

    degrees = generate_degrees(areas)
    return degrees


def cast_rays(x, y, degrees):
    samples = []
    rays = 0

    for degree in degrees:
        rays += 1

        # casting half of the rays
        if (rays % 2) == 0:
            def draw_ray(degree):
                degree -= 90

                rad = math.radians(degree)

                length = width * 1.5

                pos = int(x + length * math.cos(rad)), int(y + length * math.sin(rad))

                return pos

            end_pos = draw_ray(degree)

            # # visualization
            # img = cv2.line(image, (x, y), end_pos, (255, 0, 0), 1)

            light_points = []
            wall_points = []

            def intersection_point(objects, type):
                if type == 0:
                    for object in objects:
                        point = intersection(object[0][0], object[0][1], object[1][0], object[1][1], x, y, end_pos[0],
                                             end_pos[1])

                        if point:
                            light_points.append(point)
                elif type == 1:
                    for object in objects:
                        point = intersection(object[0][0], object[0][1], object[1][0], object[1][1], x, y, end_pos[0],
                                             end_pos[1])

                        if point:
                            wall_points.append(point)

            # for now we assume every light is white
            intersection_point(lights, 0)

            def closest_point():
                distances = []

                for point in light_points:
                    distances.append(int(np.sqrt(abs(x - point[0]) ** 2 + abs(y - point[1]) ** 2)))

                for point in wall_points:
                    distances.append(int(np.sqrt(abs(x - point[0]) ** 2 + abs(y - point[1]) ** 2)))

                # returns "light" only if light was the nearest intersection
                if np.argmin(distances) <= (len(light_points) - 1) != -1:
                    return 0

            if light_points:
                intersection_point(walls, 1)

                if wall_points:
                    samples.append(closest_point())
                else:
                    samples.append(0)
    return samples, rays


walls, walls_points, lights, lights_points = draw_room()
cv2.imshow("Map", image)
cv2.waitKey(0)
cv2.destroyAllWindows()

print("Rendering... ({})".format(dt.datetime.now().strftime("%H:%M")))


def render():
    for y in tqdm(range(height)):
        for x in range(width):
            if np.all(image[y, x] == 50):
                degrees = define_areas(x, y)
                samples, rays = cast_rays(x, y, degrees)

                # how many 0 (lights)
                intensity = samples.count(0) / 90 + (random.random() / 20)
                if intensity > 1:
                    intensity = 1
                value = 255 * intensity

                image[y, x] = (value, value, value)


render()

print("Finished ({})".format(dt.datetime.now().strftime("%H:%M")))

image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
cv2.destroyAllWindows()

now = dt.datetime.now()
datetime = str(now.strftime("%d-%m %H-%M"))
filename = "Render_v2 {} {} ".format((height, width), datetime)
cv2.imwrite("Renders\\{}.png".format(filename), image)

cv2.imshow("Rendered", image)
cv2.waitKey(0)