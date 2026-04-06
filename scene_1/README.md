# Scene 1

The scene is an aquarium with a spinning filter, swimming fish and inflating pufferfish.

## Execution
To run the scene simply download all dependencies and run aquarium.py

## Controls
Z and A - moves fish through the aquarium

A and S - inflates and deflates pufferfish

D - toggles filter fan rotation

P - toggles mesh mode
    # 'D' Stops or starts fan rotation
    if key == glfw.KEY_D and action == glfw.PRESS:
        v_angle = 0.0 if v_angle != 0.0 else 0.2
    
    # 'A' Inflates the pufferfish, 'S' deflates it, with limits to avoid extreme sizes
    elif key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        s_pufferfish = min(s_pufferfish + 0.05, 1.0)
    elif key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        s_pufferfish = max(s_pufferfish - 0.05, 0.5)
    
    # 'Z' Moves the fish left, 'X' moves it right. Releasing the keys stops the movement.
    elif key == glfw.KEY_Z:
        if action == glfw.PRESS or action == glfw.REPEAT:
            fish_velocity = -fish_speed
            fish_facing = -1.0
        elif action == glfw.RELEASE and fish_velocity < 0:
            fish_velocity = 0.0
    elif key == glfw.KEY_X:
        if action == glfw.PRESS or action == glfw.REPEAT:
            fish_velocity = fish_speed
            fish_facing = 1.0
        elif action == glfw.RELEASE and fish_velocity > 0:
            fish_velocity = 0.0
    
    # 'P' Toggles mesh mode

## Limitations

We couldn't use camera, textures or shaders and we self-imposed the limitation of writing our own code for vertex and faces generations, that meant not using third party 3D modelling software.

## Files
*.txt files store vertice coordinates and faces (defined by connecting vertices indexes) of different objects.

fish.txt was the only one written by hand, the remaining objects are generated in the scripts named gen_{object name}.py

utils.py contain utility functions that were cluttering the main aquarium.py code

## Screenshots

![Screenshot 1](./images/Screenshot1.png)

![Screenshot 2](./images/Screenshot2.png)