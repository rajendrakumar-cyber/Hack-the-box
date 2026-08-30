import { useEffect, useRef, useState } from 'react'

const WIDTH = 960
const HEIGHT = 540
const PLAYER_WIDTH = 86
const PLAYER_HEIGHT = 106
const START_CASTLE = { x: 437, y: 416, direction: 'right' }
const START_INSIDE = { x: 437, y: 416, direction: 'right' }
const GATE_LANE = { left: 384, right: 576 }
const CASTLE_GROUND_MIN_FEET_Y = 470
const CASTLE_GATE_MIN_FEET_Y = 300
const CASTLE_GATE_ENTER_FEET_Y = 462
const INSIDE_UP_LIMIT = 56
const GUARD_HEIGHT = 150
const GUARD_REFERENCE_HEIGHT = 570
const GUARDS = [
  { feetX: 328, feetY: 502, direction: 'right' },
  { feetX: 638, feetY: 502, direction: 'left' }
]
const GUARD_FRAMES = [
  { x: 220, y: 35, width: 293, height: 565 },
  { x: 830, y: 9, width: 291, height: 561 },
  { x: 1433, y: 29, width: 293, height: 570 }
]
const NPC_FRAME_ROWS = [
  {
    referenceHeight: 96,
    frames: [
      { x: 51, y: 20, width: 56, height: 95, anchorX: 28, anchorY: 95 },
      { x: 155, y: 20, width: 53, height: 95, anchorX: 26.5, anchorY: 95 },
      { x: 259, y: 19, width: 52, height: 96, anchorX: 26, anchorY: 96 }
    ]
  },
  {
    referenceHeight: 98,
    frames: [
      { x: 53, y: 133, width: 49, height: 98, anchorX: 24.5, anchorY: 98 },
      { x: 154, y: 134, width: 52, height: 97, anchorX: 26, anchorY: 97 },
      { x: 257, y: 133, width: 48, height: 98, anchorX: 24, anchorY: 98 }
    ]
  },
  {
    referenceHeight: 98,
    frames: [
      { x: 40, y: 245, width: 61, height: 98, anchorX: 30.5, anchorY: 98 },
      { x: 143, y: 244, width: 60, height: 98, anchorX: 30, anchorY: 98 },
      { x: 247, y: 244, width: 61, height: 98, anchorX: 30.5, anchorY: 98 }
    ]
  },
  {
    referenceHeight: 94,
    frames: [
      { x: 48, y: 359, width: 58, height: 93, anchorX: 29, anchorY: 93 },
      { x: 146, y: 359, width: 61, height: 94, anchorX: 30.5, anchorY: 94 },
      { x: 252, y: 359, width: 54, height: 93, anchorX: 27, anchorY: 93 }
    ]
  },
  {
    referenceHeight: 102,
    frames: [
      { x: 53, y: 468, width: 47, height: 102, anchorX: 23.5, anchorY: 102 },
      { x: 156, y: 469, width: 48, height: 101, anchorX: 24, anchorY: 101 },
      { x: 256, y: 469, width: 48, height: 101, anchorX: 24, anchorY: 101 }
    ]
  }
]
const INSIDE_NPCS = [
  { row: 1, feetX: 270, feetY: 405, height: 90 },
  { row: 3, feetX: 560, feetY: 448, height: 84 },
  { row: 4, feetX: 730, feetY: 428, height: 87 }
]
const FLAG_NPC_INDEX = 1
const NPC_INTERACTION_DISTANCE = 76
const CHARACTER_FRAMES = {
  idle: {
    referenceHeight: 123,
    duration: 260,
    frames: [
      { x: 40, y: 21, width: 89, height: 123 },
      { x: 181, y: 21, width: 84, height: 123 },
      { x: 320, y: 21, width: 82, height: 123 },
      { x: 453, y: 21, width: 81, height: 123 }
    ]
  },
  walk: {
    referenceHeight: 110,
    duration: 130,
    frames: [
      { x: 32, y: 168, width: 98, height: 108, referenceHeight: 108 },
      { x: 176, y: 168, width: 95, height: 112, referenceHeight: 112 },
      { x: 317, y: 168, width: 108, height: 111, referenceHeight: 111 },
      { x: 447, y: 168, width: 94, height: 109, referenceHeight: 109 }
    ]
  }
}

async function api(path, options = {}) {
  const headers = {
    'content-type': 'application/json',
    ...(options.headers ?? {})
  }

  const response = await fetch(path, {
    ...options,
    credentials: 'same-origin',
    headers
  })
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message ?? 'Request failed')
  }

  return data
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = src
  })
}

function isTypingTarget(target) {
  if (!(target instanceof HTMLElement)) return false

  return (
    target.isContentEditable ||
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.tagName === 'SELECT'
  )
}

function drawPixelRect(ctx, x, y, width, height, color) {
  ctx.fillStyle = color
  ctx.fillRect(Math.round(x), Math.round(y), width, height)
}

function getPlayerFeet(player) {
  return {
    x: player.x + PLAYER_WIDTH / 2,
    y: player.y + PLAYER_HEIGHT
  }
}

function isInGateLane(player) {
  const feet = getPlayerFeet(player)

  return feet.x >= GATE_LANE.left && feet.x <= GATE_LANE.right
}

function isNearNpc(player, npc) {
  const feet = getPlayerFeet(player)

  return Math.hypot(feet.x - npc.feetX, feet.y - npc.feetY) <=
    NPC_INTERACTION_DISTANCE
}

function getCanvasMetrics(viewport) {
  const scale = Math.max(viewport.width / WIDTH, viewport.height / HEIGHT)

  return {
    scale,
    offsetX: (viewport.width - WIDTH * scale) / 2,
    offsetY: (viewport.height - HEIGHT * scale) / 2
  }
}

function getNpcBubbleStyle(npc, viewport) {
  const animation = NPC_FRAME_ROWS[npc.row]
  const frame = animation.frames[0]
  const npcScale = npc.height / animation.referenceHeight
  const npcRight = npc.feetX + (frame.width - frame.anchorX) * npcScale
  const npcTop = npc.feetY - frame.anchorY * npcScale
  const canvas = getCanvasMetrics(viewport)
  const bubbleWidth = Math.min(280, viewport.width - 24)
  const x = npcRight + 14
  const y = npcTop - 8

  return {
    left: `${clamp(
      canvas.offsetX + x * canvas.scale,
      12,
      viewport.width - bubbleWidth - 12
    )}px`,
    top: `${clamp(canvas.offsetY + y * canvas.scale, 12, viewport.height - 160)}px`
  }
}

function drawStatus(ctx, status, color = '#101624') {
  const y = 68

  ctx.font = '20px monospace'
  ctx.textAlign = 'center'
  ctx.lineWidth = 4
  ctx.strokeStyle = 'rgba(248, 250, 252, 0.8)'
  ctx.strokeText(status, WIDTH / 2, y)
  ctx.fillStyle = color
  ctx.fillText(status, WIDTH / 2, y)
}

function drawCover(ctx, image, focusX = 0.5) {
  if (!image) {
    ctx.fillStyle = '#101624'
    ctx.fillRect(0, 0, WIDTH, HEIGHT)
    return
  }

  const sourceRatio = image.width / image.height
  const targetRatio = WIDTH / HEIGHT
  let sourceWidth = image.width
  let sourceHeight = image.height
  let sourceX = 0
  let sourceY = 0

  if (sourceRatio > targetRatio) {
    sourceWidth = image.height * targetRatio
    sourceX = (image.width - sourceWidth) * focusX
  } else {
    sourceHeight = image.width / targetRatio
    sourceY = (image.height - sourceHeight) / 2
  }

  ctx.drawImage(
    image,
    sourceX,
    sourceY,
    sourceWidth,
    sourceHeight,
    0,
    0,
    WIDTH,
    HEIGHT
  )
}

function drawCastle(ctx, assets, gateOpen, status) {
  drawCover(ctx, gateOpen ? assets.castleOpen : assets.castleClosed)
  drawStatus(ctx, status)
}

function drawInside(ctx, assets, status) {
  drawCover(ctx, assets.castleInside)
  drawStatus(ctx, status, '#17202a')
}

function drawInsideNpcs(ctx, assets) {
  const sheet = assets.npcs

  for (const npc of INSIDE_NPCS) {
    const animation = NPC_FRAME_ROWS[npc.row]
    const frame =
      animation.frames[
        Math.floor((performance.now() + npc.row * 130) / 360) %
          animation.frames.length
    ]
    const scale = npc.height / animation.referenceHeight
    const drawWidth = Math.round(frame.width * scale)
    const drawHeight = Math.round(frame.height * scale)
    const drawX = Math.round(npc.feetX - frame.anchorX * scale)
    const drawY = Math.round(npc.feetY - frame.anchorY * scale)

    if (!sheet) {
      drawPixelRect(ctx, drawX + 12, drawY + 8, 24, 48, '#2d7a9a')
      drawPixelRect(ctx, drawX + 16, drawY, 18, 16, '#f2c08d')
      continue
    }

    ctx.drawImage(
      sheet,
      frame.x,
      frame.y,
      frame.width,
      frame.height,
      drawX,
      drawY,
      drawWidth,
      drawHeight
    )
  }
}

function drawGuards(ctx, assets) {
  const sheet = assets.guard
  const frame =
    GUARD_FRAMES[Math.floor(performance.now() / 320) % GUARD_FRAMES.length]
  const scale = GUARD_HEIGHT / GUARD_REFERENCE_HEIGHT
  const drawWidth = Math.round(frame.width * scale)
  const drawHeight = Math.round(frame.height * scale)

  for (const guard of GUARDS) {
    const drawX = Math.round(guard.feetX - drawWidth / 2)
    const drawY = Math.round(guard.feetY - drawHeight)

    if (!sheet) {
      drawPixelRect(ctx, drawX + 14, drawY + 8, 26, 52, '#98a6b3')
      drawPixelRect(ctx, drawX + 20, drawY, 18, 14, '#e5edf5')
      continue
    }

    ctx.save()

    if (guard.direction === 'left') {
      ctx.scale(-1, 1)
      ctx.drawImage(
        sheet,
        frame.x,
        frame.y,
        frame.width,
        frame.height,
        -drawX - drawWidth,
        drawY,
        drawWidth,
        drawHeight
      )
    } else {
      ctx.drawImage(
        sheet,
        frame.x,
        frame.y,
        frame.width,
        frame.height,
        drawX,
        drawY,
        drawWidth,
        drawHeight
      )
    }

    ctx.restore()
  }
}

function drawPlayer(ctx, assets, player) {
  const sheet = assets.character

  if (!sheet) {
    drawPixelRect(ctx, player.x + 22, player.y + 8, 28, 18, '#b8c7c7')
    drawPixelRect(ctx, player.x + 18, player.y + 26, 34, 34, '#7d8c96')
    drawPixelRect(ctx, player.x + 54, player.y + 34, 10, 36, '#d7d1ad')
    drawPixelRect(ctx, player.x + 18, player.y + 60, 12, 18, '#56646f')
    drawPixelRect(ctx, player.x + 42, player.y + 60, 12, 18, '#56646f')
    return
  }

  const animation = player.moving
    ? CHARACTER_FRAMES.walk
    : CHARACTER_FRAMES.idle
  const frame =
    animation.frames[
      Math.floor(performance.now() / animation.duration) %
        animation.frames.length
    ]
  const referenceHeight = frame.referenceHeight ?? animation.referenceHeight
  const scale = PLAYER_HEIGHT / referenceHeight
  const anchorX = frame.anchorX ?? frame.width / 2
  const anchorY = frame.anchorY ?? frame.height
  const drawWidth = Math.round(frame.width * scale)
  const drawHeight = Math.round(frame.height * scale)
  const feet = getPlayerFeet(player)
  const drawX = Math.round(
    feet.x -
      (player.direction === 'left' ? frame.width - anchorX : anchorX) * scale
  )
  const drawY = Math.round(feet.y - anchorY * scale)

  ctx.save()

  if (player.direction === 'left') {
    ctx.scale(-1, 1)
    ctx.drawImage(
      sheet,
      frame.x,
      frame.y,
      frame.width,
      frame.height,
      -drawX - drawWidth,
      drawY,
      drawWidth,
      drawHeight
    )
  } else {
    ctx.drawImage(
      sheet,
      frame.x,
      frame.y,
      frame.width,
      frame.height,
      drawX,
      drawY,
      drawWidth,
      drawHeight
    )
  }

  ctx.restore()
}

function resolveCastleMovement(player, next, gateOpen) {
  const resolved = { ...next }
  const feet = getPlayerFeet(resolved)
  const currentFeet = getPlayerFeet(player)

  if (!gateOpen) {
    resolved.y = player.y
    resolved.blocked =
      resolved.x === player.x &&
      feet.y !== currentFeet.y

    return resolved
  }

  const canUseGatePath = gateOpen && isInGateLane(resolved)
  const minFeetY = canUseGatePath
    ? CASTLE_GATE_MIN_FEET_Y
    : CASTLE_GROUND_MIN_FEET_Y

  if (feet.y < minFeetY) {
    resolved.y = player.y
  }

  const resolvedFeet = getPlayerFeet(resolved)
  const isAboveGround = resolvedFeet.y < CASTLE_GROUND_MIN_FEET_Y

  if (gateOpen && isAboveGround) {
    if (resolvedFeet.x < GATE_LANE.left || resolvedFeet.x > GATE_LANE.right) {
      resolved.x = player.x
    }

    resolved.x = clamp(
      resolved.x,
      GATE_LANE.left - PLAYER_WIDTH / 2,
      GATE_LANE.right - PLAYER_WIDTH / 2
    )
  }

  resolved.blocked =
    resolved.x === player.x &&
    resolved.y === player.y &&
    (feet.x !== currentFeet.x || feet.y !== currentFeet.y)

  return resolved
}

function resolveInsideMovement(next) {
  return {
    ...next,
    y: clamp(
      next.y,
      START_INSIDE.y - INSIDE_UP_LIMIT,
      START_INSIDE.y
    )
  }
}

export function App() {
  const canvasRef = useRef(null)
  const keysRef = useRef(new Set())
  const playerRef = useRef({ ...START_CASTLE })
  const sceneRef = useRef('castle')
  const musicRef = useRef(null)
  const gateEntryPendingRef = useRef(false)
  const flagDialogVisibleRef = useRef(false)
  const assetsRef = useRef({
    character: null,
    guard: null,
    npcs: null,
    castleClosed: null,
    castleOpen: null,
    castleInside: null
  })
  const authRef = useRef({ loggedIn: false, gateOpen: false, insideGate: false })
  const loginVisibleRef = useRef(false)

  const [login, setLogin] = useState({ username: '', password: '' })
  const [loginVisible, setLoginVisible] = useState(false)
  const [loggedIn, setLoggedIn] = useState(false)
  const [gateOpen, setGateOpen] = useState(false)
  const [insideGate, setInsideGate] = useState(false)
  const [scene, setScene] = useState('castle')
  const [status, setStatus] = useState('Reach the gate. Higher privilege required.')
  const [loginError, setLoginError] = useState('')
  const [musicEnabled, setMusicEnabled] = useState(true)
  const [flagDialogVisible, setFlagDialogVisible] = useState(false)
  const [flagValue, setFlagValue] = useState('')
  const [flagError, setFlagError] = useState('')
  const [flagLoading, setFlagLoading] = useState(false)
  const [viewportSize, setViewportSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  })

  useEffect(() => {
    authRef.current = { loggedIn, gateOpen, insideGate }
  }, [loggedIn, gateOpen, insideGate])

  useEffect(() => {
    sceneRef.current = scene
  }, [scene])

  useEffect(() => {
    loginVisibleRef.current = loginVisible
  }, [loginVisible])

  useEffect(() => {
    flagDialogVisibleRef.current = flagDialogVisible
  }, [flagDialogVisible])

  useEffect(() => {
    const onResize = () => {
      setViewportSize({
        width: window.innerWidth,
        height: window.innerHeight
      })
    }

    window.addEventListener('resize', onResize)

    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    const audio = musicRef.current

    if (!audio) return

    audio.volume = 0.32

    if (!musicEnabled) {
      audio.pause()
      return
    }

    let disposed = false
    const play = () => {
      if (!disposed) {
        audio.play().catch(() => {
          // Browsers may block autoplay until the first user gesture.
        })
      }
    }

    play()
    window.addEventListener('pointerdown', play, { once: true })
    window.addEventListener('keydown', play, { once: true })

    return () => {
      disposed = true
      window.removeEventListener('pointerdown', play)
      window.removeEventListener('keydown', play)
    }
  }, [musicEnabled])

  useEffect(() => {
    Promise.all([
      loadImage('/assets/img/player-lyra-spritesheet.png'),
      loadImage('/assets/img/gate-guardian-spritesheet.png'),
      loadImage('/assets/img/town-npcs-spritesheet.png'),
      loadImage('/assets/img/castle-gate-closed.png'),
      loadImage('/assets/img/castle-gate-open.png'),
      loadImage('/assets/img/castle-interior-background.png')
    ]).then(([character, guard, npcs, castleClosed, castleOpen, castleInside]) => {
      assetsRef.current = {
        character,
        guard,
        npcs,
        castleClosed,
        castleOpen,
        castleInside
      }
    })
  }, [])

  useEffect(() => {
    api('/api/me')
      .then((result) => {
        setLoggedIn(true)
        setGateOpen(Boolean(result.gateOpen))
        setInsideGate(Boolean(result.insideGate))
        setLoginVisible(false)
        if (result.insideGate) {
          sceneRef.current = 'inside'
          setScene('inside')
          playerRef.current = { ...START_INSIDE }
          setStatus('You are inside the castle.')
        } else if (result.gateOpen) {
          setStatus('Gate authority confirmed. The way is open.')
        }
      })
      .catch(() => {
        setLoggedIn(false)
        setGateOpen(false)
        setInsideGate(false)
      })
  }, [])

  useEffect(() => {
    const onKeyDown = (event) => {
      if (isTypingTarget(event.target)) {
        keysRef.current.clear()
        return
      }

      keysRef.current.add(event.key.toLowerCase())
    }
    const onKeyUp = (event) => {
      if (isTypingTarget(event.target)) {
        keysRef.current.clear()
        return
      }

      keysRef.current.delete(event.key.toLowerCase())
    }
    const onFocusIn = (event) => {
      if (isTypingTarget(event.target)) {
        keysRef.current.clear()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    window.addEventListener('focusin', onFocusIn)

    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
      window.removeEventListener('focusin', onFocusIn)
    }
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let last = performance.now()
    let animationId

    const tick = (now) => {
      const delta = Math.min((now - last) / 1000, 0.05)
      last = now

      const keys = keysRef.current
      const player = playerRef.current
      const speed = 150
      let dx = 0
      let dy = 0

      if (keys.has('arrowleft') || keys.has('a')) dx -= 1
      if (keys.has('arrowright') || keys.has('d')) dx += 1
      if (keys.has('arrowup') || keys.has('w')) dy -= 1
      if (keys.has('arrowdown') || keys.has('s')) dy += 1

      if (loginVisibleRef.current) {
        player.moving = false
        dx = 0
        dy = 0
      }

      const triesLockedGate =
        sceneRef.current === 'castle' &&
        !authRef.current.gateOpen &&
        dy < 0 &&
        isInGateLane(player)

      if (triesLockedGate) {
        keys.clear()
        player.moving = false
        playerRef.current = {
          ...player,
          y: START_CASTLE.y,
          moving: false
        }
        loginVisibleRef.current = true
        setLoginVisible(true)
        setStatus('The guards demand authority at the gate.')
        dx = 0
        dy = 0
      }

      if (sceneRef.current === 'castle' && !authRef.current.gateOpen) {
        dy = 0
      }

      if (dx || dy) {
        const length = Math.hypot(dx, dy)
        const next = {
          x: player.x + (dx / length) * speed * delta,
          y: player.y + (dy / length) * speed * delta,
          direction:
            dx < 0
              ? 'left'
              : dx > 0
                ? 'right'
                : player.direction ?? 'right'
        }

        next.x = clamp(next.x, 18, WIDTH - PLAYER_WIDTH - 18)
        next.y = clamp(next.y, 80, HEIGHT - PLAYER_HEIGHT - 18)
        next.moving = true

        if (sceneRef.current === 'castle') {
          const resolved = resolveCastleMovement(
            player,
            next,
            authRef.current.gateOpen
          )
          const feet = getPlayerFeet(resolved)
          const enteringGate =
            authRef.current.gateOpen &&
            isInGateLane(resolved) &&
            feet.y <= CASTLE_GATE_ENTER_FEET_Y

          if (enteringGate) {
            if (!gateEntryPendingRef.current) {
              gateEntryPendingRef.current = true
              keys.clear()
              playerRef.current = { ...resolved, moving: false }
              setStatus('Requesting passage through the gate...')

              api('/api/gate/enter', {
                method: 'POST',
                body: '{}'
              })
                .then(() => {
                  setInsideGate(true)
                  authRef.current = {
                    ...authRef.current,
                    insideGate: true
                  }
                  sceneRef.current = 'inside'
                  setScene('inside')
                  playerRef.current = {
                    ...START_INSIDE,
                    x: clamp(resolved.x, 18, WIDTH - PLAYER_WIDTH - 18),
                    direction: resolved.direction,
                    moving: false
                  }
                  setStatus('You entered the castle.')
                })
                .catch((error) => {
                  gateEntryPendingRef.current = false
                  playerRef.current = {
                    ...resolved,
                    y: START_CASTLE.y,
                    moving: false
                  }
                  setStatus(error.message ?? 'The gate denies passage.')
                })
            }
          } else if (resolved.blocked) {
            setStatus(
              authRef.current.gateOpen
                ? 'Stay on the open gate path.'
                : 'The closed gate blocks the way.'
            )
            playerRef.current = { ...resolved, moving: false }
          } else {
            playerRef.current = resolved
          }
        } else {
          playerRef.current = resolveInsideMovement(next)
        }
      } else {
        player.moving = false
      }

      const nearFlagNpc =
        sceneRef.current === 'inside' &&
        isNearNpc(playerRef.current, INSIDE_NPCS[FLAG_NPC_INDEX])

      if (nearFlagNpc !== flagDialogVisibleRef.current) {
        flagDialogVisibleRef.current = nearFlagNpc
        setFlagDialogVisible(nearFlagNpc)

        if (nearFlagNpc) {
          setFlagError('')
          setStatus('A townsfolk lowers their voice.')
        }
      }

      ctx.imageSmoothingEnabled = false
      ctx.clearRect(0, 0, WIDTH, HEIGHT)

      if (sceneRef.current === 'castle') {
        drawCastle(ctx, assetsRef.current, authRef.current.gateOpen, status)
        drawGuards(ctx, assetsRef.current)
      } else {
        drawInside(ctx, assetsRef.current, status)
        drawInsideNpcs(ctx, assetsRef.current)
      }

      drawPlayer(ctx, assetsRef.current, playerRef.current)
      animationId = requestAnimationFrame(tick)
    }

    animationId = requestAnimationFrame(tick)

    return () => cancelAnimationFrame(animationId)
  }, [status])

  async function handleLogin(event) {
    event.preventDefault()
    setLoginError('')
    setStatus('Requesting authority from server...')

    try {
      const result = await api('/api/login', {
        method: 'POST',
        body: JSON.stringify(login)
      })

      setLoggedIn(true)
      setGateOpen(Boolean(result.gateOpen))
      setInsideGate(false)
      setLoginVisible(false)
      setLogin({ username: '', password: '' })
      setStatus('Gate authority confirmed. The way is open.')
    } catch {
      setLoggedIn(false)
      setGateOpen(false)
      setInsideGate(false)
      setLoginError('Access denied')
      setLoginVisible(true)
      setStatus('The gate remains sealed.')
    }
  }

  function handleCancelLogin() {
    keysRef.current.clear()
    setLoginVisible(false)
    setLoginError('')
    setLogin({ username: '', password: '' })
    playerRef.current = {
      ...playerRef.current,
      y: START_CASTLE.y,
      moving: false
    }
    setStatus('You step back from the guarded gate.')
  }

  async function handleLogout() {
    try {
      await api('/api/logout', {
        method: 'POST',
        body: '{}'
      })
    } catch {
      // Ignore logout transport failures; local state should still reset.
    }

    setLoggedIn(false)
    setGateOpen(false)
    setInsideGate(false)
    setLoginVisible(false)
    setFlagDialogVisible(false)
    setFlagValue('')
    setFlagError('')
    gateEntryPendingRef.current = false
    flagDialogVisibleRef.current = false
    setScene('castle')
    sceneRef.current = 'castle'
    playerRef.current = { ...START_CASTLE }
    setStatus('The gate is sealed again.')
  }

  async function handleAskFlag() {
    setFlagLoading(true)
    setFlagError('')

    try {
      const result = await api('/api/flag', {
        method: 'POST',
        body: '{}'
      })

      setFlagValue(result.flag)
      setStatus('The townsfolk shares the castle secret.')
    } catch (error) {
      setFlagError(error.message ?? 'No secret was shared.')
      setStatus('The townsfolk refuses to speak.')
    } finally {
      setFlagLoading(false)
    }
  }

  function handleToggleMusic() {
    setMusicEnabled((current) => {
      const next = !current
      const audio = musicRef.current

      if (audio) {
        if (next) {
          audio.volume = 0.32
          audio.play().catch(() => {
            // Playback will retry on the next interaction if needed.
          })
        } else {
          audio.pause()
        }
      }

      return next
    })
  }

  const flagNpc = INSIDE_NPCS[FLAG_NPC_INDEX]
  const npcBubbleStyle = getNpcBubbleStyle(flagNpc, viewportSize)

  return (
    <main className="game-shell">
      <section className="game-frame">
        <audio
          ref={musicRef}
          src="/assets/img/medieval-castle-loop.mp3"
          loop
          preload="auto"
        />

        <canvas
          ref={canvasRef}
          width={WIDTH}
          height={HEIGHT}
          aria-label="Gatery"
        />

        <div className="hud">
          <div className={gateOpen ? 'badge open' : 'badge'}>
            {gateOpen ? 'Gate open' : 'Gate locked'}
          </div>
          <button
            className={musicEnabled ? 'music-button active' : 'music-button'}
            type="button"
            aria-pressed={musicEnabled}
            onClick={handleToggleMusic}
          >
            {musicEnabled ? 'Music on' : 'Music off'}
          </button>
        </div>

        {scene === 'castle' && !loggedIn && loginVisible && (
          <div className="login-overlay">
            <form className="login-panel" onSubmit={handleLogin}>
              <label>
                User
                <input
                  autoComplete="username"
                  value={login.username}
                  onChange={(event) =>
                    setLogin((current) => ({
                      ...current,
                      username: event.target.value
                    }))
                  }
                />
              </label>
              <label>
                Pass
                <input
                  autoComplete="current-password"
                  type="password"
                  value={login.password}
                  onChange={(event) =>
                    setLogin((current) => ({
                      ...current,
                      password: event.target.value
                    }))
                  }
                />
              </label>
              <div className="login-actions">
                <button type="submit">Authenticate</button>
                <button type="button" onClick={handleCancelLogin}>
                  Cancel
                </button>
              </div>
              {loginError && <p>{loginError}</p>}
            </form>
          </div>
        )}

        {scene === 'inside' && flagDialogVisible && (
          <div className="npc-dialog thought-bubble" style={npcBubbleStyle}>
            <p>The townsfolk recognizes your passage through the gate.</p>
            {flagValue ? (
              <code>{flagValue}</code>
            ) : (
              <button
                type="button"
                disabled={flagLoading}
                onClick={handleAskFlag}
              >
                {flagLoading ? 'Asking...' : 'Ask for flag'}
              </button>
            )}
            {flagError && <p className="dialog-error">{flagError}</p>}
          </div>
        )}

        {loggedIn && (
          <button className="logout-button" type="button" onClick={handleLogout}>
            Logout
          </button>
        )}
      </section>
    </main>
  )
}
