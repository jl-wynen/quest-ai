use nalgebra as na;

pub type Coord = i64;
pub type Pos = na::Point2<Coord>;

pub type GridCoord = usize;
pub type GridPos = na::Point2<GridCoord>;

pub type WorldCoord = f64;
pub type WorldPos = na::Point2<WorldCoord>;

/// Like Into but only for positions.
/// Allows int/float conversions not otherwise allowed by Into.
pub trait IntoPos<T> {
    fn into_pos(self) -> T;
}

impl IntoPos<GridPos> for Pos {
    fn into_pos(self) -> GridPos {
        GridPos::new(self.x as usize, self.y as usize)
    }
}
