use nalgebra as na;

pub type Coord = i64;
pub type Pos = na::Point2<Coord>;

pub type GridCoord = usize;
pub type GridPos = na::Point2<GridCoord>;

pub type WorldCoord = f64;
pub type WorldPos = na::Point2<WorldCoord>;

pub const GRID_SCALE: usize = 4;
const SCALE: Coord = GRID_SCALE as Coord;

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
        Pos::new(
            self.x as Coord / SCALE + SCALE / 2,
            self.y as Coord / SCALE + SCALE / 2,
        )
    }
}

impl IntoPos<GridPos> for WorldPos {
    fn into_pos(self) -> GridPos {
        GridPos::new(
            self.x as GridCoord / GRID_SCALE,
            self.y as GridCoord / GRID_SCALE,
        )
    }
}
