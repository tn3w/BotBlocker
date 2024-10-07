import cv2
import math
import numpy as np
import random
import base64

def generate_captcha_with_cut():
    img_height, img_width = 500, 800
    num_circles, circle_radius, dim_alpha = 20, 60, 0.5
    cut_chance, bright_cut = 0.25, True
    background_color = (24, 24, 24)
    background = np.full((img_height, img_width, 3), background_color, dtype=np.uint8)
    bright_points = random.randint(200, 400)
    dim_points = random.randint(50, 100)

    def create_separating_cut(img, center, radius):
        cx, cy = center
        cut_angle = random.uniform(0, 2 * np.pi)
        preserve_points = generate_random_points(center, radius // 2, random.randint(10, 30))

        for theta in np.linspace(cut_angle - np.pi / 3, cut_angle, 400):
            for r in np.linspace(0, radius, 50):
                x, y = int(cx + r * np.cos(theta)), int(cy + r * np.sin(theta))
                if 0 <= x < img_width and 0 <= y < img_height:
                    img[y, x] = background_color

        for point in preserve_points:
            random_color = tuple(random.randint(100, 150) for _ in range(3))
            cv2.circle(img, point, 1, random_color, -1)

    def generate_random_points(center, radius, num_points):
        points = []
        for _ in range(num_points):
            r = radius * np.sqrt(random.random())
            theta = random.uniform(0, 2 * np.pi)
            x = int(center[0] + r * np.cos(theta))
            y = int(center[1] + r * np.sin(theta))
            points.append((x, y))
        return points

    def is_overlapping(center1, center2, radius):
        return np.linalg.norm(np.array(center1) - np.array(center2)) < (1.5 * radius)

    circle_positions, cut_circle_pos = [], None

    for _ in range(num_circles):
        while True:
            x, y = random.randint(circle_radius, img_width - circle_radius), random.randint(circle_radius, img_height - circle_radius)
            if not any(is_overlapping((x, y), pos, circle_radius) for pos in circle_positions):
                circle_positions.append((x, y))
                break

        is_bright = random.random() > 0.5
        num_points = bright_points if is_bright else dim_points
        circle_points = generate_random_points((x, y), circle_radius, num_points)

        for point in circle_points:
            random_color = tuple(random.randint(0, 255) for _ in range(3))
            cv2.circle(background, point, 1, random_color, -1)

        if not is_bright:
            overlay = np.zeros_like(background, dtype=np.uint8)
            for point in circle_points:
                random_color = tuple(random.randint(0, 255) for _ in range(3))
                cv2.circle(overlay, point, 1, random_color, -1)
            background = cv2.addWeighted(background, 1, overlay, dim_alpha, 0)

        has_cut = False
        if not is_bright and random.random() < cut_chance:
            has_cut = True
        elif is_bright and bright_cut:
            has_cut = True
            bright_cut = False

        if has_cut:
            cut_circle_pos = (x, y)
            create_separating_cut(background, (x, y), circle_radius)

    _, buffer = cv2.imencode('.webp', background, [int(cv2.IMWRITE_WEBP_QUALITY), 80])
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return {
        "image_base64": f"data:image/webp;base64,{img_base64}",
        "cut_circle_position": (cut_circle_pos[0], cut_circle_pos[1], circle_radius)
    }

def is_point_in_circle(x, y, circle_center_x, circle_center_y, circle_radius):
    distance = math.sqrt((x - circle_center_x) ** 2 + (y - circle_center_y) ** 2)

    return distance <= circle_radius


result = generate_captcha_with_cut()
print(result)
