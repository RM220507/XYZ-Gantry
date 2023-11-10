from gantrycontrol.position import Position, Position_2D
from gantrycontrol.gantry import Gantry

import json
import os.path
from gpiozero import AngularServo
from RPi.GPIO import GPIO
import time

class PuzzleBuildingRobot(Gantry):
    def __init__(self):
        super().__init__()
        self.servo = AngularServo(5, min_angle=0, max_angle=180, min_pulse_width=0.0003, max_pulse_width=0.0025)
        
        self.vacuum = 7
        GPIO.setup(self.vacuum, GPIO.OUT)
        GPIO.output(self.vacuum, GPIO.LOW)
        
        self.action_button = 11
        GPIO.setup(self.action_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        self.arrangement = None
        self.pieces_processed = False
        
        self.can_pickup = False
        
    def load_arrangement(self, path):
        if not os.path.exists(path):
            print("Command not executed: arrangement file not found")
            return
            
        with open(path, "r") as f:
            self.arrangement = json.load(f)
            
        self.pickup_coordinates = Position(50, 140, 0)
        self.fully_ext_dist2base = 0
        self.piece_spacing = 20
        self.assembly_start_pos = Position_2D(650, 270)
        
        self.can_pickup = True

        if self.fully_ext_dist2base > self.piece_height:
            print("Gantry Error: Will NEVER pick-up piece - destination surpasses limits")
            self.can_pickup = False
        else:
            self.pickup_z = self.limits.z - (self.piece_height - self.fully_ext_dist2base)
            
    def process_pieces(self):
        if not self.arrangement:
            print("Command not executed: arrangement not loaded")
            return
        
        puzzle_size = self.arrangement["puzzle-size"]
        piece_size = self.arrangement["piece-size"]
        offsets = self.arrangement["offsets"]
        
        self.pieces = [0 for i in range(puzzle_size[0] * puzzle_size[1])]
        initial_store = Position_2D(self.pickup_coordinates.x + 100, 10)
        x_spacing = self.piece_spacing + piece_size[0]
        y_spacing = self.piece_spacing + piece_size[1]
        pieces_per_column = self.limits.y // y_spacing

        for i in range(len(self.pieces)):
            print("Waiting for Piece: ", i)

            self.goto(self.pickup_coordinates)

            print("Place Piece on guide and press ActionButton")
            
            while not GPIO.input(self.action_button):
                continue
            
            print("Input Recieved - Collecting Piece")

            # pickup point
            pickup_offset = self.pickup_coordinates.copy()
            pickup_offset.x += (offsets[i][1] + (piece_size[0] // 2))
            pickup_offset.y -= (offsets[i][0] + (piece_size[1] // 2))

            # destination
            current_column = i // pieces_per_column
            dest_x = initial_store.x + (current_column * x_spacing)

            current_row = i % pieces_per_column
            dest_y = initial_store.y + (current_row * y_spacing)
            destination = Position(dest_x, dest_y, 0)
            
            # actually moving
            print("Storing Piece", i, "@", destination.x, destination.y)
            self.move_piece(pickup_offset, destination, 0)
            self.pieces[i] = destination
            
        print("Pieces loaded")
    
    def assemble_puzzle(self):
        if not self.pieces_processed:
            print("Command not executed: pieces have not yet been loaded")
            return
        
        piece_size = self.arrangement["piece-size"]
        
        for i in range(len(self.arrangement)):
            for j in range(len(self.arrangement[i])):
                piece = self.arrangement[i][j]
                piece_id = piece["id"]
                print(f"Placing Piece {piece_id} @ PuzzlePosition {i} {j}")

                storage_location = self.pieces[piece_id]

                dest_x = self.assembly_start_pos.x + (j * piece_size[0])
                dest_y = self.assembly_start_pos.y + (i * piece_size[1])
                destination = Position(dest_x, dest_y, 0)

                print(f"Moving Piece {piece_id} FROM: {storage_location.x} {storage_location.y}; TO: {destination.x} {destination.y} @ rotation {piece['rotation']}")
                
                self.move_piece(storage_location, destination, piece["rotation"])
                self.pieces[piece_id] = destination
    
    def move_piece(self, original_location, destination, rotation):
        print("Moving Piece:", original_location.x, original_location.y, "to", destination.x, destination.y)

        self.servo.angle = 0
        if rotation == 3:
            self.servo.angle = 90

        self.goto(original_location)
        
        self.pick_up()
        
        if rotation == 1:
            self.servo.angle = 90
        elif rotation == 2:
            self.servo.angle = 180
        elif rotation == 3:
            self.servo.angle = 0

        self.goto(destination)
        self.put_down()
        
    def pick_up(self):
        if self.can_pickup:
            destination = Position(self.position.x, self.position.y, self.pickup_z)
            self.goto(destination)
            
            GPIO.output(self.vacuum, GPIO.HIGH)
            time.sleep(2)
            
            self.goto(Position(self.position.x, self.position.y, 0))
        else:
            print("Gantry Error: Cannot pick-up piece - destination surpasses limits")

    def put_down(self):
        if self.can_pickup:
            destination = Position(self.position.x, self.position.y, self.pickup_z)
            self.goto(destination)
            
            GPIO.output(self.vacuum, GPIO.LOW)
            time.sleep(10)
            
            self.goto(Position(self.position.x, self.position.y, 0))
        else:
            print("Gantry Error: Cannot put down piece - destination surpasses limits")
            
    def addon_command_processing(self, command_list):
        if command_list[0] == "load-arrangement":
            self.load_arrangement(command_list[1])
        elif command_list[0] == "load-pieces":
            self.process_pieces()
        elif command_list[0] == "assemble":
            self.assemble_puzzle()
        else:
            print("Invalid command")