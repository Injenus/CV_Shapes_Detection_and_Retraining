from shapely.geometry import Polygon, Point
from shapely.affinity import rotate
import random
from PIL import Image, ImageDraw
import math
import os
import json


class ShapeGenerator:
    def __init__(self, output_dir, image_size=256):
        self.output_dir = output_dir
        self.image_size = image_size
        self.shapes = ["circle", "triangle", "rhombus", "hexagon"]
        self.image = Image.new("RGB", (image_size, image_size),
                               self._random_background_color())
        self.draw = ImageDraw.Draw(self.image)
        self.shape_data = []
        self.occupied_polygons = []

    def _random_background_color(self):
        return (
            random.randint(0, 255), random.randint(0, 255),
            random.randint(0, 255))

    def _random_shape_color(self, background_color):
        while True:
            color = (random.randint(0, 255), random.randint(0, 255),
                     random.randint(0, 255))
            if color != background_color:
                return color

    def _generate_non_overlapping_position(self, size):
        x = random.randint(int(size * 0.5), self.image_size - int(size * 0.5))
        y = random.randint(int(size * 0.5), self.image_size - int(size * 0.5))
        # print(x, y, size)
        return x, y

    def _generate_non_overlapping_polygon(self, shape_type, size, x, y,
                                          rotation):
        if shape_type == "circle":
            polygon = Point(x, y).buffer(size / 2)
        elif shape_type == "triangle":
            # # Генерируем вершины треугольника
            # points = [(x + size / 2, y), (x, y + size), (x + size, y + size)]
            # polygon = Polygon(points)
            # Генерируем вершины треугольника на окружности радиуса size/2
            angle1 = random.uniform(0, 2 * math.pi)
            angle2 = random.uniform(0, 2 * math.pi)
            angle3 = random.uniform(0, 2 * math.pi)
            radius = size / 2
            x1 = x + radius * math.cos(angle1)
            y1 = y + radius * math.sin(angle1)
            x2 = x + radius * math.cos(angle2)
            y2 = y + radius * math.sin(angle2)
            x3 = x + radius * math.cos(angle3)
            y3 = y + radius * math.sin(angle3)
            points = [(x1, y1), (x2, y2), (x3, y3)]
            polygon = Polygon(points)
        elif shape_type == "rhombus":
            # Генерируем вершины ромба
            a = random.randint(25, size)
            b = random.randint(25, size)
            points = [
                (x, y + a / 2),
                (x + b / 2, y),
                (x, y - a / 2),
                (x - b / 2, y),
            ]
            polygon = Polygon(points)
        elif shape_type == "hexagon":
            # Генерируем вершины шестиугольника равномерно распределенные по окружности радиуса size/2
            num_vertices = 6
            radius = size / 2
            hexagon_points = []
            for i in range(num_vertices):
                angle = 2 * math.pi * i / num_vertices
                x_vertex = x + radius * math.cos(angle)
                y_vertex = y + radius * math.sin(angle)
                hexagon_points.append((x_vertex, y_vertex))
            polygon = Polygon(hexagon_points)

        rotated_polygon = rotate(polygon, rotation, origin=(x, y))
        return rotated_polygon

    def _is_polygon_vacant(self, polygon):
        expanded_polygon = polygon.buffer(1)  # Добавляем 1 пиксель к периметру фигуры
        for occupied_polygon in self.occupied_polygons:
            if expanded_polygon.intersects(occupied_polygon):
                return False
        return True

    def _mark_polygon_as_occupied(self, polygon):
        self.occupied_polygons.append(polygon)

    def _draw_polygon(self, shape_type, polygon, color):
        points = list(polygon.exterior.coords)
        self.draw.polygon(points, fill=color, outline=None)

    def _draw_bounding_rectangle(self, polygon):
        min_x, min_y, max_x, max_y = polygon.bounds
        rectangle = Polygon(
            [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])
        self.draw.rectangle(rectangle.bounds, outline="red", width=1)

    def _generate_shape(self):
        shape_type = random.choice(self.shapes)
        polygon = None
        isSucces = False
        while not isSucces:
            try:
                size = random.randint(25, 150)
                x, y = self._generate_non_overlapping_position(size)
                isSucces = True
            except ValueError:
                isSucces = False

            rotation = random.uniform(0, 360)

            background_color = self._random_background_color()
            shape_color = self._random_shape_color(background_color)

            polygon = self._generate_non_overlapping_polygon(shape_type, size,
                                                             x, y, rotation)

            min_x, min_y, max_x, max_y = polygon.bounds
            shape_data_x = round(min_x)
            shape_data_y = round(min_y)
            shape_data_w = round(max_x - min_x)
            shape_data_h = round(max_y - min_y)

            if shape_data_w < 25 or shape_data_w > 150 or shape_data_h < 25 or shape_data_h > 150:
                # Размеры не соответствуют требованиям, перегенерируем фигуру
                isSucces = False

            else:
                isSucces = True

            if self._is_polygon_vacant(polygon):
                self._mark_polygon_as_occupied(polygon)
                self._draw_polygon(shape_type, polygon, shape_color)
                # self._draw_bounding_rectangle(
                #     polygon)  # Рисуем прямоугольник вокруг фигуры

                self.shape_data.append(
                    {"name": shape_type, "x": shape_data_x, "y": shape_data_y,
                     "w": shape_data_w, "h": shape_data_h,
                     "rotation": round(rotation),
                     "color": shape_color})
                isSucces = True
            else:
                isSucces = False


    def generate_image(self, image_index):
        possible_counts = [1, 2, 3, 4, 5]  # Возможные количества фигур
        count = random.choice(possible_counts)  # Случайно выбираем одно из них
        print(count)
        for _ in range(count):
            self._generate_shape()

        image_filename = os.path.join(self.output_dir,
                                      f"{image_index:03d}.png")
        json_filename = os.path.join(self.output_dir,
                                     f"{image_index:03d}.json")

        # Сохраняем изображение
        self.image.save(image_filename)

        # Создаем список для JSON-данных
        json_data = []
        for idx, shape in enumerate(self.shape_data, start=1):
            json_shape = {
                "id": str(idx),
                "name": shape["name"],
                "region": {
                    "origin": {"x": shape["x"], "y": shape["y"]},
                    "size": {"width": shape["w"], "height": shape["h"]}
                }
            }
            json_data.append(json_shape)

        # Сохраняем JSON-данные
        with open(json_filename, "w") as json_file:
            json.dump(json_data, json_file, indent=4)

        # print(f"Generated image: {image_filename}")
        # print(f"Generated JSON: {json_filename}")


# Путь к директории, в которой нужно сохранить изображения и JSON-файлы
output_directory = "examples"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Генерируем 100 пар изображений и JSON-файлов
for i in range(1, 101):
    # Создаем экземпляр класса ShapeGenerator
    generator = ShapeGenerator(output_directory)
    # Генерируем изображение с фигурами и получаем данные о фигурах
    generator.generate_image(i)

    # Выводим текущий номер генерации
    print(f"Generated pair {i}/100")
