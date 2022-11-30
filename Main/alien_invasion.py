import sys

import pygame

from time import sleep

from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from gameStats import GameStats 
from button import Button
from scoreboard import Scoreboard

class AlienInvasion:
    """Overall class to manage game assets and behavior"""

    def __init__(self):
        """Initialize the game, and create game resources"""
        pygame.init
        self.settings = Settings()
        self.bullets = pygame.sprite.Group()

        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        self.stats = GameStats(self)
        self.sb = Scoreboard(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()
        self.play_button = Button(self, "Play")

    def run_game(self):
        """Start the main loop for the game"""
        while True:
            self._check_events()
            if self.stats.game_active:
                self.ship.update()
                self.__update_bullets()
                self._update_aliens()
            self.__update_screen__()
               
    def _check_events(self):
        """Respond to keypresses and mouse events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_Keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
                
    def _check_play_button(self, mouse_pos):
        """start a new game when the player press play"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            #reset the play button
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.aliens.empty()
            self.bullets.empty()
            self._create_fleet()
            self.ship.center_ship()
            pygame.mouse.set_visible(False)
            self.sb.prep_ships()

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_q:
            sys.exit()

    def _check_Keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullet group"""
        if len(self.bullets) < self.settings.bullets_allowed:   
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def __update_screen__(self):
        self.screen.fill(self.settings.bg_color)
        self.screen.blit(self.settings.bg_image, (0,0))
        

        #Calling the function to draw image when the game starts
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()

        

        #make th most recent drawn screen visible
        self.aliens.draw(self.screen)
        self.sb.show_score()

        #Draw the play button if the game is inactive
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()
        
    def __update_bullets(self):
        """Update posistion of bullets and delete old bullets"""
        self.bullets.update()
        #get rid of old bullets
        for bullet in self.bullets.copy():
                if bullet.rect.bottom <= 0:
                    self.bullets.remove(bullet)
                    print(len(self.bullets))
        self._Check_bullet_and_collision()

    def _update_aliens(self):
        self.check_fleet_edges()
        self.aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit_()

        self._check_aliens_bottom()

    def _create_fleet(self):
        """Create the fleet of aliens"""
        #make an alien
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        availible_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = availible_space_x // (2 * alien_width)

        #determine the number of rows of aliens that fit on the screen
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - 
                                (3* alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        #Create first row of aliens.
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                #Create an alien and place it in the row
                self._create_alien(alien_number, row_number)
            
    def _create_alien(self, alien_number, row_number):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def check_fleet_edges(self):
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_directon()
                break

    def _change_fleet_directon(self):
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _Check_bullet_and_collision(self):
        """Respond to bullet-alien collision"""
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.stats.score += self.settings.alien_points
            self.sb.prep_score()
            self.sb.check_high_score()


        if not self.aliens:
            #Destroy exsisting bullets and creatr new fleet
            self.bullets.empty()
            self._create_fleet()
            # Increase level.
            self.stats.level += 1
            self.sb.prep_level()

    def _ship_hit_(self):
        """respond to ship being hit by alien"""
        #decrement ships left
        if self.stats.ship_left > 0:
            self.stats.ship_left -= 1
            self.sb.prep_ships()
            #get rid off any remaining aliens and bullets
            self.aliens.empty()
            self.bullets.empty()
            #Create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()
            #Pause
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                #treat this the same as if ship got hit.
                self._ship_hit_()
                break

if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()