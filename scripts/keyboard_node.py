#!/usr/bin/env python
# coding=utf-8
"""
    File:
        keyboard_node.py

    Description:
        Simple python routine to watch the keyboard or a joystick
    to send velocity commands to a Gazebo simulation

    Author:
        Felipe Gomes de Melo <felipegmelo@usp.br>
"""

import pygame
import argparse
import sys

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64

# Vamos acompanhar o estado dessas teclas
KEYS = [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]

# Indice dos eixos x e y do joystick
X_AXIS = 4
Y_AXIS = 0
ARMA_AXIS = 5
INVERT_X_AXIS = False
INVERT_Y_AXIS = True
INVERT_ARMA_AXIS = True

ROBOTS = 1

# Namespace dos tópicos que iremos publicar
DEFAULT_NAMESPACE = "/thunder_line_follower_pmr3100"

DEFAULT_DEBUG = False

# A vel máxima do robô é 2 m/s
LIN_VEL = 1  # m/s
WHEEL_RADIUS = 0.030  # m

ANG_VEL = LIN_VEL / WHEEL_RADIUS  # rad/s
ANG_VEL = 120  # ras/s

ARMA_ANG_VEL = 200  # rad/s

# Os comandos vão de -126 até 126 de modo que os bytes 0xFE e 0xFF
# nunca são utilizados
SCALE = 126


def getNamespace(number):
    return DEFAULT_NAMESPACE.format(number + 1)


def drawConsole(win, font, console):
    """
    Fills window console with the sentences stored in the list console
        :param win: pygame.display Window object to be filled
        :param font: pygame.Font Font style to be used
        :param console: list<font.render> List of text to write
    """
    img = font.render("Event console Area", 1, (155, 155, 155), (0, 0, 0))
    win.blit(img, (2, 132))
    ypos = 450
    h = list(console)
    h.reverse()
    for line in h:
        r = win.blit(line, (10, ypos))
        win.fill(0, (r.right, r.top, 620, r.height))
        ypos -= font.get_height()


def main(namespace, debug=DEFAULT_DEBUG):

    vel_pub = None
    vel_msg = None
    rate = None
    current_robot = 0

    # Inicia configs do ROS
    rospy.init_node("human_controller")

    vel_pub_dir = []
    vel_pub_esq = []
    arma_pub = []

    for i in range(ROBOTS):
        vel_pub_dir.append(
            rospy.Publisher(
                getNamespace(i) + "/robot_right_controller/command",
                Float64,
                queue_size=2,
            )
        )
        vel_pub_esq.append(
            rospy.Publisher(
                getNamespace(i) + "/robot_left_controller/command",
                Float64,
                queue_size=2,
            )
        )
        arma_pub.append(
            rospy.Publisher(
                getNamespace(i) + "/arma_controller/command", Float64, queue_size=2
            )
        )

    rate = rospy.Rate(60)  # 60hz

    pygame.init()

    # Cria a janela
    win = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
    pygame.display.set_caption("nRFDongle Comunication Interface")

    # Lista de frases a serem mostradas no console
    console = []
    font = pygame.font.Font(None, 26)

    # Dicionário para guardar o estado de algumas teclas
    state = {}
    for key in KEYS:
        state[key] = False

    # Vamos detectar os Joysticks conectados ao computador
    axis = [0.0, 0.0, 0.0]
    using_joystick = True
    for x in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(x)
        j.init()
        txt = "Enabled joystick: " + j.get_name()
        print(txt)
        img = font.render(txt, 1, (50, 200, 50), (0, 0, 0))
        console.append(img)

    if not pygame.joystick.get_count():
        using_joystick = False
        print("No Joysticks to Initialize")
        img = font.render("No Joysticks to Initialize", 1, (50, 200, 50), (0, 0, 0))
        console.append(img)

    running = True
    while running:

        for e in pygame.event.get():

            # Movimento dos botões do teclado
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                if e.key in KEYS:
                    state[e.key] = True
            elif e.type == pygame.KEYUP:
                if e.key in KEYS:
                    state[e.key] = False

            # Movimento dos direcionais do joystick
            if e.type == pygame.JOYAXISMOTION:
                if e.dict["axis"] in (X_AXIS, Y_AXIS, ARMA_AXIS):
                    if e.dict["axis"] == X_AXIS:
                        if INVERT_X_AXIS:
                            axis[0] = -e.value
                        else:
                            axis[0] = e.value

                    elif e.dict["axis"] == Y_AXIS:
                        if INVERT_Y_AXIS:
                            axis[1] = -e.value
                        else:
                            axis[1] = e.value

                    elif e.dict["axis"] == ARMA_AXIS:
                        if INVERT_ARMA_AXIS:
                            axis[2] = -e.value
                        else:
                            axis[2] = e.value

            # Caso algum botão do joystick seja apertado
            if (
                e.type == pygame.JOYBUTTONDOWN
                or e.type == pygame.JOYBUTTONUP
                or e.type == pygame.JOYHATMOTION
            ):

                txt = "%s: %s" % (pygame.event.event_name(e.type), e.dict)
                print(txt)
                img = font.render(txt, 1, (50, 200, 50), (0, 0, 0))
                console.append(img)
                console = console[-13:]

            # L1 pressionado
            if (e.type == pygame.JOYBUTTONDOWN and e.dict["button"] == 4) or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_e
            ):
                current_robot += 1
                current_robot %= ROBOTS

            if (e.type == pygame.JOYBUTTONDOWN and e.dict["button"] == 5) or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_q
            ):
                current_robot -= 1
                current_robot %= ROBOTS

            elif e.type == pygame.VIDEORESIZE:
                win = pygame.display.set_mode(e.size, pygame.RESIZABLE)

            elif e.type == pygame.QUIT:
                running = False

        drawConsole(win, font, console)
        pygame.display.flip()

        if using_joystick:
            txt = "X: {} Y: {}".format(int(axis[0] * SCALE), int(axis[1] * SCALE))
            if debug:
                print(txt)
                img = font.render(txt, 1, (50, 200, 50), (0, 0, 0))
                console.append(img)
                console = console[-13:]

            vel_dir = Float64((axis[1] - axis[0]) * ANG_VEL / 2)
            vel_esq = Float64((axis[1] + axis[0]) * ANG_VEL / 2)
            vel_arma = Float64((axis[2] - 1) * ARMA_ANG_VEL / 2)

            vel_pub_dir[current_robot].publish(vel_dir)
            vel_pub_esq[current_robot].publish(vel_esq)
            arma_pub[current_robot].publish(vel_arma)

        else:
            vel_x = 0.0
            if state[pygame.K_w]:
                vel_x += 1.0
            if state[pygame.K_s]:
                vel_x -= 1.0

            vel_y = 0.0
            if state[pygame.K_a]:
                vel_y += 1.0
            if state[pygame.K_d]:
                vel_y -= 1.0

            txt = "X: {} Y: {}".format(int(vel_x * SCALE), int(vel_y * SCALE))
            if debug:
                print(txt)
                img = font.render(txt, 1, (50, 200, 50), (0, 0, 0))
                console.append(img)
                console = console[-13:]

            vel_dir = Float64((vel_y - vel_x) * ANG_VEL / 2)
            vel_esq = Float64((vel_y + vel_x) * ANG_VEL / 2)

            vel_pub_dir[current_robot].publish(vel_dir)
            vel_pub_esq[current_robot].publish(vel_esq)

        rate.sleep()


if __name__ == "__main__":
    rospy.loginfo("Começando a brincadeira!")

    # Clean ROS parameters from command line
    myargv = rospy.myargv(argv=sys.argv)

    # parser = argparse.ArgumentParser()
    # parser.add_argument("-n", "--namespace", type=str,
    #                     default=DEFAULT_NAMESPACE)
    # parser.add_argument("-d", "--debug", action="store_true")

    print(myargv)
    rospy.loginfo(myargv)

    # args = parser.parse_args(myargv)

    main(DEFAULT_NAMESPACE)
