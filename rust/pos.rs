use nalgebra as na;

pub type Coord = i64;
pub type Pos = na::Point2<Coord>;

pub type GridCoord = usize;
pub type GridPos = na::Point2<GridCoord>;

pub type WorldCoord = f64;
pub type WorldPos = na::Point2<WorldCoord>;

pub const WORLD_SCALE: usize = 1;
const SCALE: Coord = WORLD_SCALE as Coord;

/// Like Into but only for positions.
/// Allows int/float conversions not otherwise allowed by Into.
pub trait IntoPos<T> {
    fn into_pos(self) -> T;
}

impl IntoPos<GridPos> for Pos {
    fn into_pos(self) -> GridPos {
        GridPos::new(self.x as GridCoord, self.y as GridCoord)
    }
}

impl IntoPos<WorldPos> for Pos {
    fn into_pos(self) -> WorldPos {
        WorldPos::new(
            (self.x * SCALE) as WorldCoord,
            (self.y * SCALE) as WorldCoord,
        )
    }
}

impl IntoPos<Pos> for WorldPos {
    fn into_pos(self) -> Pos {
        Pos::new(self.x as Coord / SCALE, self.y as Coord / SCALE)
    }
}
