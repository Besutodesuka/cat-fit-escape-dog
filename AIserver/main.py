import cv2
from time import time
from math import hypot
import mediapipe as mp
from pose_estimator import detectLandmark, checkLeftRight, checkJumpCrouch, checkHandsJoined

import socket

mp_pose = mp.solutions.pose

# code for unity request
positions = {
    "left": -1,
    "center": 0,
    "right": 1
}
actions = {
    "standing": 0,
    "slide": 1,
    "jump": 2
}
gamemodes = {
    "mainmenu": 0,
    "ingame": 1,
    "gameover": 2,
    "pause": 3
}

# Initialize the VideoCapture object to read from the webcam.
camera_video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera_video.set(3, 1280)
camera_video.set(4, 960)

# Create named window for resizing purposes.
cv2.namedWindow('PuddingMaprawnon2', cv2.WINDOW_NORMAL)

#initial localhost server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serveraddr = ("127.0.0.1", 5202)

# Initialize a variable to store the time of the previous frame.
time1 = 0

# Initialize a variable to store the state of the game (started or not).
game_started = False

# Initialize a variable to store the index of the current horizontal position of the person.
# At Start the character is at center so the index is 1 and it can move left (value 0) and right (value 2).
x_pos_index = 1

# Initialize a variable to store the index of the current vertical posture of the person.
# At Start the person is standing so the index is 1 and he can crouch (value 0) and jump (value 2).
y_pos_index = 1

# Declate a variable to store the intial y-coordinate of the mid-point of both shoulders of the person.
MID_Y = None

# Initialize a counter to store count of the number of consecutive frames with person's hands joined.
counter = 0

# Initialize the number of consecutive frames on which we want to check if person hands joined before starting the game.
frame_countdown = 10

# Iterate until the webcam is accessed successfully.
action = 0
position = 0
gamemode = 0
while camera_video.isOpened():
    # Read a frame.
    ok, frame = camera_video.read()

    # Check if frame is not read properly then continue to the next iteration to read the next frame.
    if not ok:
        continue

    # Flip the frame horizontally for natural (selfie-view) visualization.
    frame = cv2.flip(frame, 1)

    # Get the height and width of the frame of the webcam video.
    frame_height, frame_width, _ = frame.shape

    # Perform the pose detection on the frame.
    frame, results = detectLandmark(frame, draw=game_started)

    # Check if the pose landmarks in the frame are detected.
    if results.pose_landmarks:

        # detect position of person for unity overlay
        # --------------------------------------------------------------------------------------------------------------

        # Get horizontal position of the person in the frame.
        frame, horizontal_position = checkLeftRight(frame, results, draw=True)
        if horizontal_position == 'Center':
            position = positions["center"]
        # Check if the person has moved to left from center or to center from right.
        elif (horizontal_position == 'Left' and x_pos_index != 0) or (
                horizontal_position == 'Center' and x_pos_index == 2):

            # Press the left arrow key.
            # pyautogui.press('left')
            position = positions["left"]

            # Update the horizontal position index of the character.
            x_pos_index -= 1

            # Check if the person has moved to Right from center or to center from left.
        elif (horizontal_position == 'Right' and x_pos_index != 2) or (
                horizontal_position == 'Center' and x_pos_index == 0):

            # Press the right arrow key.
            # pyautogui.press('right')

            position = positions["right"]

            # Update the horizontal position index of the character.
            x_pos_index += 1

        # --------------------------------------------------------------------------------------------------------------
        # Command to Start or resume the game.
        # ------------------------------------------------------------------------------------------------------------------

        if not game_started:
            cv2.putText(frame, "please join your hand together to start the game", (150, 480), cv2.FONT_HERSHEY_PLAIN, 2,
                        (0, 0, 0),
                        3)

        # Check if the left and right hands are joined.
        if checkHandsJoined(frame, results)[1] == 'Hands Joined':

            # Increment the count of consecutive frames with +ve condition.
            counter += 1

            # Check if the counter is equal to the required number of consecutive frames.
            if counter == frame_countdown:
                # Command to Start the game first time.
                # ----------------------------------------------------------------------------------------------------------
                # Check if the game has not started yet.
                # continue to play game from pause menu
                if not (game_started):
                    # Update the value of the variable that stores the game state.
                    game_started = True
                    # update wait time so the time use for pausing will be 7/fps = 1 sec
                    frame_countdown = 7

                    gamemode = gamemodes["ingame"]

                    # Retreive the y-coordinate of the left shoulder landmark.
                    left_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * frame_height)

                    # Retreive the y-coordinate of the right shoulder landmark.
                    # Retreive the y-coordinate of the right shoulder landmark.
                    right_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * frame_height)

                    # Calculate the intial y-coordinate of the mid-point of both shoulders of the person.
                    MID_Y = abs(right_y + left_y) // 2 - 30


                # ----------------------------------------------------------------------------------------------------------
                # Command to resume the game after death of the character.
                # ----------------------------------------------------------------------------------------------------------

                # Otherwise if the game has started.(going to pause the game)
                else:
                    # Update game state to pause
                    game_started = False
                    gamemode = gamemodes["pause"]
                    # update wait time so the time use for pausing will be 30/fps = 3 sec
                    frame_countdown = 30

                    # Press the space key.
                    # pyautogui.press('space')

                # ----------------------------------------------------------------------------------------------------------

                # Update the counter value to zero. (reset charge time)
                counter = 0

        # Otherwise if the left and right hands are not joined.
        else:

            # Update the counter value to zero.
            counter = 0

        # ------------------------------------------------------------------------------------------------------------------

        # Commands to control the vertical movements of the character.
        # ------------------------------------------------------------------------------------------------------------------

        # Check if the intial y-coordinate of the mid-point of both shoulders of the person has a value.
        if MID_Y:

            # Get posture (jumping, crouching or standing) of the person in the frame.
            frame, posture = checkJumpCrouch(frame, results, MID_Y, draw=True)

            # Check if the person has jumped.
            if posture == 'Jumping' and y_pos_index == 1:

                # Press the up arrow key
                # pyautogui.press('up')

                action = actions["jump"]
                # Update the veritcal position index of  the character.
                y_pos_index += 1

                # Check if the person has crouched.
            elif posture == 'Crouching' and y_pos_index == 1:

                # Press the down arrow key
                # pyautogui.press('down')
                action = actions["slide"]

                # Update the veritcal position index of the character.
                y_pos_index -= 1

            # Check if the person has stood.
            elif posture == 'Standing' and y_pos_index != 1:

                # Update the veritcal position index of the character.
                y_pos_index = 1

                action = actions["standing"]

        # ------------------------------------------------------------------------------------------------------------------


    # Otherwise if the pose landmarks in the frame are not detected.
    else:

        # Update the counter value to zero.
        counter = 0

    # Calculate the frames updates in one second
    # ----------------------------------------------------------------------------------------------------------------------

    # Set the time for this frame to the current time.
    time2 = time()
    # Check if the difference between the previous and this frame time > 0 to avoid division by zero.
    if (time2 - time1) > 0:
        # Calculate the number of frames per second.
        frames_per_second = 1.0 / (time2 - time1)

        # Write the calculated number of frames per second on the frame.
        cv2.putText(frame, 'FPS: {}'.format(int(frames_per_second)), (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0),
                    3)

    # Update the previous frame time to this frame time.
    # As this frame will become previous frame in next iteration.
    time1 = time2

    # ----------------------------------------------------------------------------------------------------------------------

    sock.sendto(str.encode(f"{str(action)},{str(position)},{str(gamemode)}"), serveraddr)
    # Display the frame.
    cv2.imshow('PuddingMaprawnon2', frame)

    # Wait for 1ms. If a key is pressed, retreive the ASCII code of the key.
    k = cv2.waitKey(1) & 0xFF

    # Check if 'ESC' is pressed and break the loop.
    if (k == 27):
        break

# Release the VideoCapture Object and close the windows.
camera_video.release()
cv2.destroyAllWindows()