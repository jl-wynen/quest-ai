use nalgebra as na;
use ndarray::{s, Array2, ArrayView2};
use numpy::{PyArray2, ToPyArray};
use pyo3::prelude::*;

pub type GridPos = na::Point2<usize>;

pub fn to_grid_pos(p: na::Point2<i64>) -> GridPos {
    na::Point2::new(p.x as usize, p.y as usize)
}

#[pyclass(module = "janlukasAI")]
pub struct World {
    pub map: Array2<i64>,

    #[pyo3(get, set)]
    pub enemy_flag: Option<(u64, u64)>,
}

impl World {
    const EMPTY: i64 = 0;
    const OBSTACLE: i64 = 1;
    const GEM: i64 = 2;
    const NO_INFO: i64 = -1;

    pub fn is_obstacle(&self, pos: GridPos) -> bool {
        self.map
            .get((pos.x, pos.y))
            .map_or(false, |&t| t == World::OBSTACLE)
    }
    pub fn is_obstacle_or_out(&self, pos: GridPos) -> bool {
        self.map
            .get((pos.x, pos.y))
            .map_or(true, |&t| t == World::OBSTACLE)
    }

    pub fn free_neighbours_of(&self, pos: &GridPos) -> impl Iterator<Item = GridPos> {
        let mut res = Vec::new();
        for p in [
            GridPos::new(pos.x + 1, pos.y),
            GridPos::new(pos.x - 1, pos.y),
            GridPos::new(pos.x, pos.y + 1),
            GridPos::new(pos.x, pos.y - 1),
        ] {
            if !self.is_obstacle_or_out(p) {
                res.push(p);
            }
        }
        res.into_iter()
    }
}

fn local_map_start(knight_pos: GridPos, view_range: usize) -> (usize, usize) {
    let start_x = if knight_pos.x < view_range {
        0
    } else {
        knight_pos.x - view_range
    };
    let start_y = if knight_pos.y < view_range {
        0
    } else {
        knight_pos.y - view_range
    };
    (start_x, start_y)
}

impl World {
    fn incorporate_impl(
        &mut self,
        local_map: ArrayView2<i64>,
        knight_pos: GridPos,
        view_range: usize,
    ) {
        let (start_x, start_y) = local_map_start(knight_pos, view_range);
        let end_x = start_x + local_map.shape()[0];
        let end_y = start_y + local_map.shape()[1];
        let mut slice = self.map.slice_mut(s![start_x..end_x, start_y..end_y]);

        // Copy local_map into self.map
        // Extrude obstacles by 1 pixel in x and y.
        // The outer map is sliced such that indexing into `slice` with x+-1 and y+-1
        // is always valid.
        local_map
            .slice(s![1..local_map.shape()[0] - 1, 1..local_map.shape()[1] - 1])
            .indexed_iter()
            .for_each(|((x, y), &l)| {
                if l == World::OBSTACLE {
                    let x = x + 1;
                    let y = y + 1;
                    for xx in x - 1..x + 2 {
                        slice[(xx, y - 1)] = l;
                        slice[(xx, y)] = l;
                        slice[(xx, y + 1)] = l;
                    }
                }
            });
    }

    pub fn in_bounds(&self, pos: &GridPos) -> bool {
        pos.x < self.map.shape()[0] && pos.y < self.map.shape()[1]
    }
}

#[pymethods]
impl World {
    #[new]
    fn py_new(shape: (usize, usize)) -> Self {
        World {
            map: Array2::from_elem(shape, World::NO_INFO),
            enemy_flag: None,
        }
    }

    fn get_map<'py>(&self, py: Python<'py>) -> &'py PyArray2<i64> {
        self.map.to_pyarray(py)
    }

    fn incorporate(
        &mut self,
        local_map: &PyArray2<i64>,
        knight_pos: (usize, usize),
        view_range: usize,
    ) {
        let read_only_local_map = local_map.readonly();
        let knight_pos = GridPos::new(knight_pos.0, knight_pos.1);
        self.incorporate_impl(read_only_local_map.as_array(), knight_pos, view_range);
    }
}

pub fn bind(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<World>()?;
    Ok(())
}
