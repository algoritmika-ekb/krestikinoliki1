import pygame
import sys
import random
import math
import json
import os
from datetime import datetime

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
WINDOW_SIZE = 600
BOARD_SIZE = 3
CELL_SIZE = WINDOW_SIZE // BOARD_SIZE
SAVE_FILE = "tictactoe_stats.json"

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (44, 62, 80)
LIGHT_BLUE = (52, 152, 219)
RED = (231, 76, 60)
GREEN = (46, 204, 113)
PURPLE = (155, 89, 182)
GRAY = (149, 165, 166)
DARK_GRAY = (52, 73, 94)
YELLOW = (241, 196, 15)
ORANGE = (230, 126, 34)
DARK_RED = (192, 57, 43)
DARK_GREEN = (39, 174, 96)

class Particle:
    """Класс для частиц анимации"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.life = random.randint(20, 50)
        self.max_life = self.life
        self.color = random.choice([RED, LIGHT_BLUE, GREEN, YELLOW, PURPLE, ORANGE])
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0
    
    def draw(self, screen):
        alpha = self.life / self.max_life
        color = tuple(int(c * alpha) for c in self.color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

class Button:
    """Класс для кнопок меню"""
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.animation_scale = 1.0
        self.target_scale = 1.0
        
    def draw(self, screen, font):
        if self.is_hovered:
            self.target_scale = 1.05
        else:
            self.target_scale = 1.0
        
        self.animation_scale += (self.target_scale - self.animation_scale) * 0.2
        
        color = self.hover_color if self.is_hovered else self.color
        scaled_rect = self.rect.copy()
        scaled_rect.width *= self.animation_scale
        scaled_rect.height *= self.animation_scale
        scaled_rect.center = self.rect.center
        
        pygame.draw.rect(screen, color, scaled_rect, border_radius=15)
        pygame.draw.rect(screen, WHITE, scaled_rect, 3, border_radius=15)
        
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return True
        return False

class GameStats:
    """Класс для управления статистикой"""
    def __init__(self):
        self.stats = {
            "total_games": 0,
            "wins": {"X": 0, "O": 0, "draw": 0},
            "vs_friend": {"X": 0, "O": 0, "draw": 0},
            "vs_ai": {"X": 0, "O": 0, "draw": 0},
            "difficulty_stats": {
                "easy": {"X": 0, "O": 0, "draw": 0},
                "normal": {"X": 0, "O": 0, "draw": 0},
                "hard": {"X": 0, "O": 0, "draw": 0}
            },
            "last_played": None,
            "game_history": []
        }
        self.load_stats()
    
    def save_stats(self):
        """Сохраняет статистику в файл"""
        try:
            self.stats["last_played"] = datetime.now().isoformat()
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False
    
    def load_stats(self):
        """Загружает статистику из файла"""
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    loaded_stats = json.load(f)
                    # Обновляем только существующие ключи
                    for key in self.stats:
                        if key in loaded_stats:
                            self.stats[key] = loaded_stats[key]
                return True
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
        return False
    
    def add_game(self, winner, game_mode, difficulty=None):
        """Добавляет результат игры в статистику"""
        self.stats["total_games"] += 1
        
        # Общая статистика
        self.stats["wins"][winner] += 1
        
        # Статистика по режиму
        if game_mode == "friend":
            self.stats["vs_friend"][winner] += 1
        else:  # ai
            self.stats["vs_ai"][winner] += 1
            if difficulty:
                self.stats["difficulty_stats"][difficulty][winner] += 1
        
        # История игр
        game_record = {
            "date": datetime.now().isoformat(),
            "winner": winner,
            "mode": game_mode,
            "difficulty": difficulty
        }
        self.stats["game_history"].append(game_record)
        
        # Ограничиваем историю последними 100 играми
        if len(self.stats["game_history"]) > 100:
            self.stats["game_history"] = self.stats["game_history"][-100:]
        
        self.save_stats()
    
    def reset_stats(self):
        """Сбрасывает всю статистику"""
        self.__init__()
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
    
    def get_win_rate(self, mode="total"):
        """Возвращает процент побед"""
        if mode == "total":
            total = self.stats["total_games"]
            if total == 0:
                return 0
            return (self.stats["wins"]["X"] / total) * 100
        return 0

class TicTacToe:
    def __init__(self):
        # Создание окна
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 100))
        pygame.display.set_caption("Крестики-нолики")
        
        # Загрузка шрифтов
        self.font_title = pygame.font.Font(None, 72)
        self.font_big = pygame.font.Font(None, 120)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_button = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)
        
        # Инициализация статистики
        self.stats_manager = GameStats()
        
        # Состояния игры
        self.MENU = 0
        self.PLAYING = 1
        self.STATS_SCREEN = 2
        
        self.state = self.MENU
        self.difficulty = "normal"
        self.game_mode = "friend"  # friend или ai
        
        # Переменные игры
        self.board = [None] * 9
        self.current_player = "X"
        self.game_over = False
        self.winner = None
        self.winning_line = None
        
        # Частицы для анимации
        self.particles = []
        
        # Уведомление о сохранении
        self.notification_text = None
        self.notification_timer = 0
        
        # Создание кнопок меню
        self.create_menu_buttons()
        self.create_stats_buttons()
        
        # Игровые кнопки
        self.reset_button = pygame.Rect(WINDOW_SIZE//2 - 150, WINDOW_SIZE + 30, 140, 40)
        self.menu_button = pygame.Rect(WINDOW_SIZE//2 + 10, WINDOW_SIZE + 30, 140, 40)
        
        # Анимация заголовка
        self.title_angle = 0
        
        # Основной цикл
        self.clock = pygame.time.Clock()
        self.running = True
    
    def create_menu_buttons(self):
        """Создание кнопок главного меню"""
        button_width = 280
        button_height = 55
        center_x = WINDOW_SIZE // 2 - button_width // 2
        
        self.play_friend_btn = Button(
            center_x, 230, button_width, button_height,
            "Игра с другом 🤝", GREEN, DARK_GREEN
        )
        
        self.play_ai_btn = Button(
            center_x, 300, button_width, button_height,
            "Игра с компьютером 🤖", LIGHT_BLUE, (41, 128, 185)
        )
        
        self.difficulty_btn = Button(
            center_x, 370, button_width, button_height,
            "Сложность: Нормальная", PURPLE, (142, 68, 173)
        )
        
        self.stats_btn = Button(
            center_x, 440, button_width, button_height,
            "📊 Статистика", ORANGE, (214, 137, 16)
        )
        
        self.exit_btn = Button(
            center_x, 510, button_width, button_height,
            "Выход 🚪", RED, (192, 57, 43)
        )
    
    def create_stats_buttons(self):
        """Создание кнопок для экрана статистики"""
        self.back_btn = Button(
            WINDOW_SIZE//2 - 140, 530, 280, 55,
            "Назад в меню ↩️", LIGHT_BLUE, (41, 128, 185)
        )
        
        self.reset_stats_btn = Button(
            WINDOW_SIZE//2 - 140, 470, 280, 45,
            "Сбросить статистику 🗑️", RED, DARK_RED
        )
    
    def show_notification(self, text):
        """Показывает уведомление на экране"""
        self.notification_text = text
        self.notification_timer = 120  # 2 секунды при 60 FPS
    
    def draw_menu(self):
        """Отрисовка главного меню"""
        self.screen.fill(DARK_BLUE)
        
        # Анимация фона
        for i in range(50):
            x = random.randint(0, WINDOW_SIZE)
            y = random.randint(0, WINDOW_SIZE)
            color = (random.randint(30, 60), random.randint(40, 70), random.randint(80, 100))
            pygame.draw.circle(self.screen, color, (x, y), 2)
        
        # Анимированный заголовок
        self.title_angle += 0.02
        title_offset_y = math.sin(self.title_angle) * 10
        
        # Тень заголовка
        shadow_surface = self.font_title.render("КРЕСТИКИ-НОЛИКИ", True, (0, 0, 0, 128))
        shadow_rect = shadow_surface.get_rect(center=(WINDOW_SIZE//2 + 3, 113 + title_offset_y))
        self.screen.blit(shadow_surface, shadow_rect)
        
        # Основной заголовок
        title_surface = self.font_title.render("КРЕСТИКИ-НОЛИКИ", True, WHITE)
        title_rect = title_surface.get_rect(center=(WINDOW_SIZE//2, 110 + title_offset_y))
        self.screen.blit(title_surface, title_rect)
        
        # Подзаголовок
        subtitle_surface = self.font_small.render("Выберите режим игры", True, GRAY)
        subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_SIZE//2, 180))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Отрисовка кнопок
        self.play_friend_btn.draw(self.screen, self.font_button)
        self.play_ai_btn.draw(self.screen, self.font_button)
        self.difficulty_btn.draw(self.screen, self.font_button)
        self.stats_btn.draw(self.screen, self.font_button)
        self.exit_btn.draw(self.screen, self.font_button)
        
        # Статистика в меню
        stats_y = 580
        stats_surface = self.font_small.render("Краткая статистика:", True, WHITE)
        self.screen.blit(stats_surface, (WINDOW_SIZE//2 - 80, stats_y))
        
        total_games = self.stats_manager.stats["total_games"]
        wins_x = self.stats_manager.stats["wins"]["X"]
        draws = self.stats_manager.stats["wins"]["draw"]
        wins_o = self.stats_manager.stats["wins"]["O"]
        
        stats_text = f"Игр: {total_games} | X: {wins_x} | Ничьи: {draws} | O: {wins_o}"
        stats_surface = self.font_tiny.render(stats_text, True, YELLOW)
        stats_rect = stats_surface.get_rect(center=(WINDOW_SIZE//2, stats_y + 25))
        self.screen.blit(stats_surface, stats_rect)
        
        # Дата последней игры
        if self.stats_manager.stats["last_played"]:
            last_played = self.stats_manager.stats["last_played"]
            try:
                date_obj = datetime.fromisoformat(last_played)
                date_str = date_obj.strftime("%d.%m.%Y %H:%M")
                last_surface = self.font_tiny.render(f"Последняя игра: {date_str}", True, GRAY)
                self.screen.blit(last_surface, (10, WINDOW_SIZE - 20))
            except:
                pass
    
    def draw_stats_screen(self):
        """Отрисовка экрана статистики"""
        self.screen.fill(DARK_BLUE)
        
        # Заголовок
        title_surface = self.font_title.render("СТАТИСТИКА", True, WHITE)
        title_rect = title_surface.get_rect(center=(WINDOW_SIZE//2, 50))
        self.screen.blit(title_surface, title_rect)
        
        y_offset = 100
        stats = self.stats_manager.stats
        
        # Общая статистика
        self.draw_section_title("Общая статистика", y_offset)
        y_offset += 40
        
        total = stats["total_games"]
        stats_texts = [
            f"Всего игр: {total}",
            f"Побед X: {stats['wins']['X']}",
            f"Побед O: {stats['wins']['O']}",
            f"Ничьих: {stats['wins']['draw']}"
        ]
        
        if total > 0:
            win_rate = (stats['wins']['X'] / total) * 100
            stats_texts.append(f"Процент побед X: {win_rate:.1f}%")
        
        for text in stats_texts:
            surface = self.font_small.render(text, True, WHITE)
            self.screen.blit(surface, (50, y_offset))
            y_offset += 30
        
        # Статистика по режимам
        y_offset += 20
        self.draw_section_title("Игра с другом", y_offset)
        y_offset += 40
        
        vs_friend_texts = [
            f"Победы X: {stats['vs_friend']['X']}",
            f"Победы O: {stats['vs_friend']['O']}",
            f"Ничьи: {stats['vs_friend']['draw']}"
        ]
        
        for text in vs_friend_texts:
            surface = self.font_tiny.render(text, True, GRAY)
            self.screen.blit(surface, (70, y_offset))
            y_offset += 25
        
        # Статистика против компьютера
        y_offset += 10
        self.draw_section_title("Игра с компьютером", y_offset)
        y_offset += 40
        
        vs_ai_texts = [
            f"Победы X: {stats['vs_ai']['X']}",
            f"Победы O: {stats['vs_ai']['O']}",
            f"Ничьи: {stats['vs_ai']['draw']}"
        ]
        
        for text in vs_ai_texts:
            surface = self.font_tiny.render(text, True, GRAY)
            self.screen.blit(surface, (70, y_offset))
            y_offset += 25
        
        # Статистика по сложности
        y_offset += 10
        self.draw_section_title("По сложности", y_offset)
        y_offset += 40
        
        for diff, diff_stats in stats["difficulty_stats"].items():
            diff_name = {"easy": "Легкая", "normal": "Нормальная", "hard": "Сложная"}
            diff_text = f"{diff_name[diff]}: X:{diff_stats['X']} O:{diff_stats['O']} Н:{diff_stats['draw']}"
            surface = self.font_tiny.render(diff_text, True, GRAY)
            self.screen.blit(surface, (70, y_offset))
            y_offset += 25
        
        # Кнопки
        self.back_btn.draw(self.screen, self.font_button)
        self.reset_stats_btn.draw(self.screen, self.font_small)
        
        # Подсказка
        hint_surface = self.font_tiny.render("Статистика сохраняется автоматически", True, DARK_GRAY)
        hint_rect = hint_surface.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE - 10))
        self.screen.blit(hint_surface, hint_rect)
    
    def draw_section_title(self, title, y):
        """Рисует заголовок секции статистики"""
        # Линия слева
        pygame.draw.line(
            self.screen, GRAY,
            (50, y + 20), (150, y + 20), 2
        )
        
        # Текст
        surface = self.font_small.render(title, True, YELLOW)
        self.screen.blit(surface, (160, y + 5))
        
        # Линия справа
        pygame.draw.line(
            self.screen, GRAY,
            (400, y + 20), (550, y + 20), 2
        )
    
    def draw_notification(self):
        """Рисует уведомление о сохранении"""
        if self.notification_text and self.notification_timer > 0:
            alpha = min(self.notification_timer / 30, 1.0)
            
            # Фон уведомления
            notif_surface = pygame.Surface((300, 40))
            notif_surface.set_alpha(int(200 * alpha))
            notif_surface.fill(DARK_GREEN)
            
            notif_rect = notif_surface.get_rect(
                center=(WINDOW_SIZE//2, WINDOW_SIZE + 50)
            )
            self.screen.blit(notif_surface, notif_rect)
            
            # Текст уведомления
            text_surface = self.font_tiny.render(self.notification_text, True, WHITE)
            text_surface.set_alpha(int(255 * alpha))
            text_rect = text_surface.get_rect(center=notif_rect.center)
            self.screen.blit(text_surface, text_rect)
            
            self.notification_timer -= 1
    
    def draw_board(self):
        """Отрисовка игрового поля"""
        self.screen.fill(DARK_BLUE)
        
        # Рисуем линии сетки
        for i in range(1, BOARD_SIZE):
            pygame.draw.line(
                self.screen, WHITE,
                (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE),
                5
            )
            pygame.draw.line(
                self.screen, WHITE,
                (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE),
                5
            )
        
        # Рисуем X и O
        for i in range(9):
            if self.board[i]:
                x = (i % 3) * CELL_SIZE + CELL_SIZE // 2
                y = (i // 3) * CELL_SIZE + CELL_SIZE // 2
                
                if self.board[i] == "X":
                    self.draw_x(x, y)
                else:
                    self.draw_o(x, y)
        
        # Частицы
        for particle in self.particles:
            if particle.update():
                particle.draw(self.screen)
        self.particles = [p for p in self.particles if p.life > 0]
        
        # Подсвечиваем выигрышную линию
        if self.winning_line and self.game_over:
            self.highlight_winning_line()
    
    def draw_x(self, x, y, size=None, color=None, width=None):
        """Рисуем крестик"""
        if size is None:
            size = CELL_SIZE // 3
        if color is None:
            color = RED
        if width is None:
            width = 8
        
        pygame.draw.line(
            self.screen, color,
            (x - size, y - size),
            (x + size, y + size),
            width
        )
        pygame.draw.line(
            self.screen, color,
            (x + size, y - size),
            (x - size, y + size),
            width
        )
    
    def draw_o(self, x, y, radius=None, color=None, width=None):
        """Рисуем нолик"""
        if radius is None:
            radius = CELL_SIZE // 3
        if color is None:
            color = LIGHT_BLUE
        if width is None:
            width = 8
        
        pygame.draw.circle(self.screen, color, (x, y), radius, width)
    
    def highlight_winning_line(self):
        """Подсветка выигрышной комбинации"""
        if not self.winning_line:
            return
        
        start_cell = self.winning_line[0]
        end_cell = self.winning_line[2]
        
        start_x = (start_cell % 3) * CELL_SIZE + CELL_SIZE // 2
        start_y = (start_cell // 3) * CELL_SIZE + CELL_SIZE // 2
        end_x = (end_cell % 3) * CELL_SIZE + CELL_SIZE // 2
        end_y = (end_cell // 3) * CELL_SIZE + CELL_SIZE // 2
        
        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 3 + 9
        color = GREEN if self.winner == "X" else PURPLE
        
        pygame.draw.line(
            self.screen, color,
            (start_x, start_y),
            (end_x, end_y),
            int(pulse)
        )
        
        for cell in [start_cell, end_cell]:
            x = (cell % 3) * CELL_SIZE + CELL_SIZE // 2
            y = (cell // 3) * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(self.screen, YELLOW, (x, y), 10)
    
    def draw_game_ui(self):
        """Отрисовка игрового интерфейса"""
        pygame.draw.rect(
            self.screen, DARK_GRAY,
            (0, WINDOW_SIZE, WINDOW_SIZE, 100)
        )
        
        # Статус игры
        if self.game_over:
            if self.winner:
                status_text = f"Игрок {self.winner} победил!"
                status_color = RED if self.winner == "X" else LIGHT_BLUE
            else:
                status_text = "Ничья!"
                status_color = YELLOW
        else:
            if self.game_mode == "ai" and self.current_player == "O":
                status_text = "Компьютер думает..."
                status_color = PURPLE
            else:
                status_text = f"Ход игрока {self.current_player}"
                status_color = RED if self.current_player == "X" else LIGHT_BLUE
        
        status_surface = self.font_medium.render(status_text, True, status_color)
        status_rect = status_surface.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE + 20))
        self.screen.blit(status_surface, status_rect)
        
        # Кнопки
        pygame.draw.rect(self.screen, GREEN, self.reset_button, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.reset_button, 2, border_radius=10)
        reset_text = self.font_small.render("Новая игра", True, WHITE)
        reset_rect = reset_text.get_rect(center=self.reset_button.center)
        self.screen.blit(reset_text, reset_rect)
        
        pygame.draw.rect(self.screen, ORANGE, self.menu_button, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, self.menu_button, 2, border_radius=10)
        menu_text = self.font_small.render("Меню", True, WHITE)
        menu_rect = menu_text.get_rect(center=self.menu_button.center)
        self.screen.blit(menu_text, menu_rect)
        
        # Счет
        score_y = WINDOW_SIZE + 60
        score_texts = [
            f"X: {self.stats_manager.stats['wins']['X']}",
            f"Ничьи: {self.stats_manager.stats['wins']['draw']}",
            f"O: {self.stats_manager.stats['wins']['O']}"
        ]
        score_colors = [RED, YELLOW, LIGHT_BLUE]
        
        for i, (text, color) in enumerate(zip(score_texts, score_colors)):
            score_surface = self.font_small.render(text, True, color)
            score_x = 20 + i * 200
            self.screen.blit(score_surface, (score_x, score_y))
    
    def handle_menu_click(self, pos):
        """Обработка кликов в меню"""
        if self.play_friend_btn.rect.collidepoint(pos):
            self.game_mode = "friend"
            self.state = self.PLAYING
            self.reset_game()
        elif self.play_ai_btn.rect.collidepoint(pos):
            self.game_mode = "ai"
            self.state = self.PLAYING
            self.reset_game()
        elif self.difficulty_btn.rect.collidepoint(pos):
            self.cycle_difficulty()
        elif self.stats_btn.rect.collidepoint(pos):
            self.state = self.STATS_SCREEN
        elif self.exit_btn.rect.collidepoint(pos):
            self.running = False
    
    def handle_stats_click(self, pos):
        """Обработка кликов на экране статистики"""
        if self.back_btn.rect.collidepoint(pos):
            self.state = self.MENU
        elif self.reset_stats_btn.rect.collidepoint(pos):
            self.stats_manager.reset_stats()
            self.show_notification("Статистика сброшена!")
    
    def cycle_difficulty(self):
        """Переключение сложности"""
        difficulties = ["easy", "normal", "hard"]
        difficulties_names = ["Легкая", "Нормальная", "Сложная"]
        current_index = difficulties.index(self.difficulty)
        next_index = (current_index + 1) % len(difficulties)
        self.difficulty = difficulties[next_index]
        self.difficulty_btn.text = f"Сложность: {difficulties_names[next_index]}"
    
    def handle_game_click(self, pos):
        """Обработка кликов в игре"""
        x, y = pos
        
        if y < WINDOW_SIZE and not self.game_over:
            row = y // CELL_SIZE
            col = x // CELL_SIZE
            index = row * 3 + col
            
            if self.board[index] is None:
                self.make_move(index)
                
                if (self.game_mode == "ai" and 
                    not self.game_over and self.current_player == "O"):
                    self.ai_move()
        
        elif y > WINDOW_SIZE:
            if self.reset_button.collidepoint(pos):
                self.reset_game()
            elif self.menu_button.collidepoint(pos):
                self.state = self.MENU
    
    def make_move(self, index):
        """Совершение хода"""
        self.board[index] = self.current_player
        
        # Добавляем частицы
        x = (index % 3) * CELL_SIZE + CELL_SIZE // 2
        y = (index // 3) * CELL_SIZE + CELL_SIZE // 2
        for _ in range(20):
            self.particles.append(Particle(x, y))
        
        # Проверка победы
        winner = self.check_winner()
        if winner:
            self.game_over = True
            self.winner = winner
            # Сохраняем результат
            self.stats_manager.add_game(winner, self.game_mode, self.difficulty)
            self.show_notification("Результат сохранен!")
        elif all(cell is not None for cell in self.board):
            self.game_over = True
            self.winner = None
            self.stats_manager.add_game("draw", self.game_mode, self.difficulty)
            self.show_notification("Результат сохранен!")
        else:
            self.current_player = "O" if self.current_player == "X" else "X"
    
    def ai_move(self):
        """Ход компьютера"""
        pygame.time.wait(500)
        
        if self.difficulty == "easy":
            empty_cells = [i for i, cell in enumerate(self.board) if cell is None]
            if empty_cells:
                move = random.choice(empty_cells)
                self.make_move(move)
        elif self.difficulty == "normal":
            if random.random() < 0.7:
                self.make_best_move()
            else:
                empty_cells = [i for i, cell in enumerate(self.board) if cell is None]
                if empty_cells:
                    move = random.choice(empty_cells)
                    self.make_move(move)
        else:  # hard
            self.make_best_move()
    
    def make_best_move(self):
        """Оптимальный ход"""
        best_score = -float("inf")
        best_move = None
        
        for i in range(9):
            if self.board[i] is None:
                self.board[i] = "O"
                score = self.minimax(self.board, 0, False)
                self.board[i] = None
                
                if score > best_score:
                    best_score = score
                    best_move = i
        
        if best_move is not None:
            self.make_move(best_move)
    
    def minimax(self, board, depth, is_maximizing):
        """Алгоритм минимакс"""
        winner = self.check_winner_for_board(board)
        if winner == "O":
            return 10 - depth
        elif winner == "X":
            return depth - 10
        elif all(cell is not None for cell in board):
            return 0
        
        if is_maximizing:
            best_score = -float("inf")
            for i in range(9):
                if board[i] is None:
                    board[i] = "O"
                    score = self.minimax(board, depth + 1, False)
                    board[i] = None
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float("inf")
            for i in range(9):
                if board[i] is None:
                    board[i] = "X"
                    score = self.minimax(board, depth + 1, True)
                    board[i] = None
                    best_score = min(score, best_score)
            return best_score
    
    def check_winner_for_board(self, board):
        """Проверка победителя для переданного поля"""
        win_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        
        for combo in win_combinations:
            if (board[combo[0]] == board[combo[1]] == 
                board[combo[2]] is not None):
                return board[combo[0]]
        
        return None
    
    def check_winner(self):
        """Проверка победителя текущего поля"""
        win_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        
        for combo in win_combinations:
            if (self.board[combo[0]] == self.board[combo[1]] == 
                self.board[combo[2]] is not None):
                self.winning_line = combo
                return self.board[combo[0]]
        
        self.winning_line = None
        return None
    
    def reset_game(self):
        """Сброс игры"""
        self.board = [None] * 9
        self.current_player = "X"
        self.game_over = False
        self.winner = None
        self.winning_line = None
        self.particles = []
    
    def run(self):
        """Основной игровой цикл"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stats_manager.save_stats()  # Сохраняем при выходе
                    self.running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.state == self.MENU:
                            self.handle_menu_click(event.pos)
                        elif self.state == self.PLAYING:
                            self.handle_game_click(event.pos)
                        elif self.state == self.STATS_SCREEN:
                            self.handle_stats_click(event.pos)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == self.PLAYING:
                            self.state = self.MENU
                        elif self.state == self.STATS_SCREEN:
                            self.state = self.MENU
                        else:
                            self.stats_manager.save_stats()
                            self.running = False
                    elif event.key == pygame.K_r and self.state == self.PLAYING:
                        self.reset_game()
                
                # Обработка событий для кнопок
                if self.state == self.MENU:
                    self.play_friend_btn.handle_event(event)
                    self.play_ai_btn.handle_event(event)
                    self.difficulty_btn.handle_event(event)
                    self.stats_btn.handle_event(event)
                    self.exit_btn.handle_event(event)
                elif self.state == self.STATS_SCREEN:
                    self.back_btn.handle_event(event)
                    self.reset_stats_btn.handle_event(event)
            
            # Отрисовка в зависимости от состояния
            if self.state == self.MENU:
                self.draw_menu()
            elif self.state == self.PLAYING:
                self.draw_board()
                self.draw_game_ui()
                self.draw_notification()
            elif self.state == self.STATS_SCREEN:
                self.draw_stats_screen()
                self.draw_notification()
            
            # Обновление экрана
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# Запуск игры
if __name__ == "__main__":
    game = TicTacToe()
    game.run()