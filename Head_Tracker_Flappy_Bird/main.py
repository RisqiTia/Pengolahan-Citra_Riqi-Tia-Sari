# Import lIbrary
import sys, time, random, pygame
from collections import deque
import cv2 as cv, mediapipe as mp

# Setup Mediapipe untuk mengambil modul face mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
pygame.init()
clock = pygame.time.Clock()

# Membuka webcam dan membuat window game
VID_CAP = cv.VideoCapture(0)
window_size = (
    int(VID_CAP.get(cv.CAP_PROP_FRAME_WIDTH)),
    int(VID_CAP.get(cv.CAP_PROP_FRAME_HEIGHT))
)
screen = pygame.display.set_mode(window_size)

# Bird and Pipe Init
bird_img = pygame.image.load("bird_sprite.png")
bird_img = pygame.transform.scale(bird_img, (int(bird_img.get_width()/9), int(bird_img.get_height()/9)))
bird_frame = bird_img.get_rect()
bird_frame.center = (window_size[0] // 6, window_size[1] // 2)
pipe_frames = deque()
pipe_img = pygame.image.load("pipe_sprite_single.png")

# Resize pipe
pipe_img = pygame.transform.scale(
    pipe_img,
    (
        int(pipe_img.get_width() * 0.5),
        int(pipe_img.get_height() * 0.5)
    )
)

pipe_starting_template = pipe_img.get_rect()

# Variable Game
# Jarak antar pipe
space_between_pipes = 180

# Game Variables
game_clock = time.time()
stage = 1
pipeSpawnTimer = 0
time_between_pipe_spawn = 40
dist_between_pipes = 300
pipe_velocity = lambda: dist_between_pipes / time_between_pipe_spawn
score = 0
didUpdateScore = False
game_is_running = True

# Memulai face mash
with mp_face_mesh.FaceMesh(max_num_faces=1,
                           refine_landmarks=True,
                           min_detection_confidence=0.5,
                           min_tracking_confidence=0.5) as face_mesh:
  
  # Game looping
  while True:
    if not game_is_running:
      text = pygame.font.SysFont("Helvetica Bold.ttf", 64).render("Game Over!", True, (99, 245, 255))
      tr = text.get_rect()
      tr.center = (window_size[0]/2, window_size[1]/2)
      screen.blit(text, tr)
      pygame.display.update()
      pygame.time.wait(2000)
      VID_CAP.release()
      cv.destroyAllWindows()
      pygame.quit()
      sys.exit()

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        VID_CAP.release()
        cv.destroyAllWindows()
        pygame.quit()
        sys.exit()

    ret, frame = VID_CAP.read()
    if not ret:
      print("Empty Frame, continuing...")
      continue

    screen.fill((225,225,225))

    frame.flags.writeable = False
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = face_mesh.process(frame)
    frame.flags.writeable = True

    if results.multi_face_landmarks and len(results.multi_face_landmarks) > 0:
      marker = results.multi_face_landmarks[0].landmark[94].y
      bird_frame.centery = (marker - 0.5) * 1.5 * window_size[1] + window_size[1]/2
      if bird_frame.top < 0: bird_frame.y = 0
      if bird_frame.bottom > window_size[1]: bird_frame.y = window_size[1] - bird_frame.height


    frame = cv.flip(frame, 1).swapaxes(0,1)

    # Gerak Pipe
    for pf in pipe_frames:
      pf[0].x -= int(pipe_velocity())
      pf[1].x -= int(pipe_velocity())

    if len(pipe_frames) > 0 and pipe_frames[0][0].right < 0:
      pipe_frames.popleft()

    # Render Game
    pygame.surfarray.blit_array(screen, frame)
    screen.blit(bird_img, bird_frame)
    checker = True
    for pf in pipe_frames:
      if pf[0].left <= bird_frame.x <= pf[0].right:
        checker = False
        if not didUpdateScore:
          score += 1
          didUpdateScore = True
      screen.blit(pipe_img, pf[1])
      screen.blit(pygame.transform.flip(pipe_img, False, True), pf[0])
    if checker: didUpdateScore = False

    # Stage, Score text
    text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Stage {stage}', True, (99, 245, 255))
    tr = text.get_rect()
    tr.center = (100, 50)
    screen.blit(text, tr)
    text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Score {score}', True, (99, 245, 255))
    tr = text.get_rect()
    tr.center = (100, 100)
    screen.blit(text, tr)

    pygame.display.flip()

    #Collison Detection
    if (any([bird_frame.colliderect(pf[0]) or bird_frame.colliderect(pf[1]) for pf in pipe_frames])):
      game_is_running = False

    if pipeSpawnTimer == 0:

      gap = 160
      gap_y = random.randint(120, window_size[1] - 220)
      top = pipe_starting_template.copy()
      top.x = window_size[0]
      top.y = gap_y - pipe_img.get_height() - 50
      bottom = pipe_starting_template.copy()
      bottom.x = window_size[0]
      bottom.y = gap_y + gap - 50

      pipe_frames.append([top, bottom])
      
    pipeSpawnTimer += 1
    if pipeSpawnTimer >= time_between_pipe_spawn: pipeSpawnTimer = 0

    if time.time() - game_clock >= 10:
      time_between_pipe_spawn *= 5/6
      stage += 1
      game_clock = time.time()

# Fps Control
clock.tick(60)