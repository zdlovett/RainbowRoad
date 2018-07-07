
"""
Ideas:
Warp core:
pulse that moves in from the top and bottom and then bright 
at the gpu when it meets in the middle

Rain:
blue rain down the side, with white flashes at the top,
blue ripples on the bottom, and soft lighting from the gpu

Voice / sound based something or other



Final output is a nx3 array x times per second

Inputs are animation type and segments
Outputs to each segment are added? -> not sure about this, it will cause a bias towards lighter colors

Should output arrays be mixed in HSV space then converted before going on the wire?
 -> only useful if the output animations need to be mixed in hsv before getting converted


How should the animations be connected to each other? 
What if each animation is actually done as f(seg(s), args) -> seg? 
Then the output from each could be used to drive the others, and we could make use of a 
graph (or simular) layout for the gui when stringing animations together. 





"""
