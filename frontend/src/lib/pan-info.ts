/**
 * Minimal shape of the gesture info handed to `onDragEnd`.
 *
 * `motion@14` re-exports `framer-motion` without its type declarations, so the
 * `PanInfo` type isn't importable — this structural copy keeps us typed.
 */
export interface PanInfoLike {
  offset: { x: number; y: number };
  velocity: { x: number; y: number };
}

/** True when the drag should advance the pager to the next card/chart/month. */
export function swipedLeft(info: PanInfoLike, distance = 60, speed = 420): boolean {
  return info.offset.x < -distance || info.velocity.x < -speed;
}

/** True when the drag should go back one card/chart/month. */
export function swipedRight(info: PanInfoLike, distance = 60, speed = 420): boolean {
  return info.offset.x > distance || info.velocity.x > speed;
}
