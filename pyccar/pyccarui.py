import os
import pygame

# Colors
black = (0,0,0)
white = (255,255,255)
red   = (255,0,0)
green = (0,255,0)
blue  = (0,0,255)
grey  = (127,127,127)

# Element Types
# 1 - Back
# 2 - Exit
# 3 - Up
# 4 - Down
# 5 - Scroll
# 6 - Menu Item

def ui_redraw(bbox, element_type, flags, opt_arg):
    bBorders = flags &  1
    bActive  = flags &  2
    bEnabled = flags &  4
    bSubMenu = flags &  8
    bVisible = flags & 16
    pygame.draw.rect(screen, black, bbox, 0) # 0-thickness = fill
    if bVisible:
        (x, y, w, h) = bbox
        d = h / 10
        if w < h:
            d = w / 10
        if d < 5:
            d = 5
        if bBorders:
            color = grey
            if bEnabled:
                color = white
            thickness = 3
            if bActive:
                thickness = 9
            pygame.draw.rect(screen, color, (x+d, y+d, w-2*d, h-2*d), thickness)
        thickness = 5
        if element_type == 1:
            bboxi = (x+3*d, y+3*d, w-6*d, h-6*d)
            pygame.draw.arc(screen, color, bboxi, 0,    3.14, thickness)
            pygame.draw.arc(screen, color, bboxi, 4.71, 6.28, thickness)
            xarr = x+3*d
            yarr = y+h/2
            pygame.draw.lines(screen, color, True, [(xarr-d,yarr), (xarr+d,yarr), (xarr,yarr+d)], thickness)
        elif element_type == 2:
            bboxi = (x+3*d, y+3*d, w-6*d, h-6*d)
            pygame.draw.arc(screen, color, bboxi, 0,    1.22, thickness)
            pygame.draw.arc(screen, color, bboxi, 1.92, 6.28, thickness)
            pygame.draw.lines(screen, color, False, [(x+w/2,y+h/2), (x+w/2,y+2*d)], thickness)
        elif element_type == 3:
            xl = x + 3*d
            yt = y + 3*d
            x0 = x + w/2
            xr = x + w - 6*d
            yb = y + h - 6*d
            pygame.draw.lines(screen, color, True, [(xl,yb), (x0,yt), (xr,yb)], thickness)
        elif element_type == 4:
            xl = x + 3*d
            yt = y + 3*d
            x0 = x + w/2
            xr = x + w - 6*d
            yb = y + h - 6*d
            pygame.draw.lines(screen, color, True, [(xl,yt), (x0,yb), (xr,yt)], thickness)
        elif element_type == 5:
            bboxi = (x+d, y, w-2*d, h)
            pygame.draw.rect(screen, grey, bboxi, 0)
            if opt_arg:
                (s_min, s_max) = opt_arg
                bboxi = (x+2*d, y+(h*s_min)/100, w-4*d, (h*(s_max-s_min))/100)
                pygame.draw.rect(screen, blue, bboxi, 0)
        elif element_type == 6:
            if opt_arg:
                font  = pygame.font.Font(None, h-3*d)
                label = font.render(str(opt_arg), 1, (color))
                screen.blit(label, (x+2*d,y+2*d))
            if bSubMenu:
                xl = x + w - 6*d
                yt = y + 2*d
                y0 = y + h/2
                xr = x + w - 2*d
                yb = y + h - 2*d
                pygame.draw.lines(screen, color, True, [(xl,yt), (xl,yb), (xr,y0)], thickness)
        else:
            None


def ui_refresh():
    pygame.display.update()

def ui_init(driver, device, screen_w, screen_h):
    os.environ["SDL_VIDEODRIVER"] = driver
    os.environ["SDL_FBDEV"] = device
    pygame.init()
    pygame.display.init()
    pygame.mouse.set_visible(0)
    pygame.font.init()
    global screen
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.FULLSCREEN)
    screen.fill(black)
