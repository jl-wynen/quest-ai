use crate::path::theta_star::ThetaStar;
use crate::pos::*;
use crate::priority::PriorityQueue;
use crate::world::World;
use nalgebra as na;
use pyo3::prelude::*;

#[allow(unused)]
fn euclidean_distance(a: &Pos, b: &Pos) -> f64 {
    use nalgebra::Norm;
    let diff = a - b;
    na::EuclideanNorm {}.norm(&na::Vector2::new(diff.x as f64, diff.y as f64))
}

#[allow(unused)]
fn manhattan_distance(a: &Pos, b: &Pos) -> i64 {
    (a - b).sum()
}

fn within_one_step(a: &WorldPos, b: &WorldPos, step_length: f64) -> bool {
    use nalgebra::Norm;
    na::EuclideanNorm {}.norm(&(a - b)).abs() < step_length
}

#[pyclass]
struct Path {
    /// Target of the path in internal coordinates.
    target: Pos,
    /// Precise target in world coordinates.
    world_target: WorldPos,
    /// Current path in reverse order.
    path: Vec<WorldPos>,
    pathfinder: ThetaStar,
    /// Recompute the path in this many calls to next.
    recompute_in: i32,
}

impl Path {
    fn next_impl(
        &mut self,
        current: &WorldPos,
        world: &World,
        step_length: f64,
    ) -> Option<&WorldPos> {
        if within_one_step(current, &self.world_target, step_length) {
            return None;
        }

        if self.recompute_in == 0 {
            self.path.clear();
        }
        self.recompute_in -= 1;

        if self.path.is_empty() {
            self.find_path(current, world);
        }
        self.drop_until_not_at(current, step_length);
        self.path.last()
    }

    fn drop_until_not_at(&mut self, pos: &WorldPos, step_length: f64) {
        while let Some(top) = self.path.last() {
            if within_one_step(top, pos, step_length) {
                self.path.pop();
            } else {
                break;
            }
        }
    }

    fn find_path(&mut self, start: &WorldPos, world: &World) {
        match self
            .pathfinder
            .find_path(&start.into_pos(), &self.target, world)
        {
            None => {}
            Some(path) => {
                self.path = path;
                // Make sure the target is precise.
                self.path[0] = self.world_target;
            }
        }
    }
}

#[pymethods]
impl Path {
    #[new]
    fn new(world: &World) -> Self {
        Self {
            target: Pos::origin(),
            world_target: WorldPos::origin(),
            path: Vec::with_capacity(512),
            pathfinder: ThetaStar::new(world),
            recompute_in: 0,
        }
    }

    fn set_target(&mut self, target: (WorldCoord, WorldCoord)) {
        self.world_target = WorldPos::new(target.0, target.1);
        self.target = self.world_target.into_pos();
        self.recompute_in = 0;
    }

    fn next(
        &mut self,
        current: (WorldCoord, WorldCoord),
        world: &World,
        speed: f64,
        dt: f64,
    ) -> Option<(WorldCoord, WorldCoord)> {
        self.next_impl(&WorldPos::new(current.0, current.1), world, speed * dt)
            .map(|p| (p.x, p.y))
    }

    fn clear_path(&mut self) {
        self.path.clear();
    }

    fn recompute_in_one_turn(&mut self) {
        self.recompute_in = 1;
    }
}

pub fn bind(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<Path>()?;
    Ok(())
}

mod theta_star {
    use super::*;
    use crate::pos_map::PosMap;

    pub struct ThetaStar {
        /// Unexpanded nodes.
        /// value: node
        /// cost: cost to go to node + heuristic
        open_set: PriorityQueue<Pos, f64>,
        /// Maps node to its parent
        parents: PosMap<Pos>,
        /// Current best cost to go to node
        costs: PosMap<f64>,
    }

    impl ThetaStar {
        pub fn new(world: &World) -> Self {
            Self {
                open_set: PriorityQueue::with_capacity(2 << 11),
                parents: PosMap::new(world.shape(), Pos::new(-1, -1)),
                costs: PosMap::new(world.shape(), f64::INFINITY),
            }
        }

        pub fn clear(&mut self) {
            self.open_set.clear();
            self.parents.clear();
            self.costs.clear();
        }

        pub fn find_path(
            &mut self,
            start: &Pos,
            target: &Pos,
            world: &World,
        ) -> Option<Vec<WorldPos>> {
            if !world.in_bounds(&target.into_pos()) {
                return None;
            }

            self.clear();
            self.open_set.push(*start, 0.0);
            self.costs.set(start, 0.0);

            while let Some(current) = self.open_set.pop() {
                if target == &current {
                    break;
                }

                for neighbour in world
                    .free_neighbours_of(&current.into_pos())
                    .map(|n| Pos::new(n.x as Coord, n.y as Coord))
                {
                    let src = self.source_of(&neighbour, &current, world);
                    if neighbour == src {
                        continue;
                    }

                    let cost =
                        self.costs.get_unchecked(&src) + euclidean_distance(&src, &neighbour);
                    if cost < self.costs.get_or(&neighbour, &f64::INFINITY) {
                        let expected_cost = cost + euclidean_distance(&neighbour, target);
                        self.open_set.push(neighbour, expected_cost);
                        self.parents.set(&neighbour, src);
                        self.costs.set(&neighbour, cost);
                    }
                }
            }

            if !self.parents.is_set(target) {
                return None;
            }
            Some(self.reconstruct_path(start, target))
        }

        fn source_of(&self, node: &Pos, current: &Pos, world: &World) -> Pos {
            if let Some(parent) = self.parents.get_if_set(current) {
                if !bresenham::path_is_blocked(parent, node, world) {
                    return *parent;
                }
            }
            *current
        }

        fn reconstruct_path(&self, start: &Pos, target: &Pos) -> Vec<WorldPos> {
            let mut path = Vec::with_capacity(32);
            let mut curr = *target;
            while curr != *start {
                path.push(curr.into_pos());
                curr = self.parents.get_unchecked(&curr);
            }
            path
        }
    }
}

/// Collision detection based on Bresenham's line drawing algorithm.
mod bresenham {
    use super::*;

    pub fn path_is_blocked(p0: &Pos, p1: &Pos, world: &World) -> bool {
        let d = p1 - p0;
        if d.x.abs() > d.y.abs() {
            let (p0, p1) = if p0.x > p1.x { (p1, p0) } else { (p0, p1) };
            path_is_blocked_low(p0, p1, world)
        } else {
            let (p0, p1) = if p0.y > p1.y { (p1, p0) } else { (p0, p1) };
            path_is_blocked_high(p0, p1, world)
        }
    }

    /// For dx > dy
    fn path_is_blocked_low(p0: &Pos, p1: &Pos, world: &World) -> bool {
        let diff = p1 - p0;
        let dx = diff.x;
        let dy = diff.y.abs();
        let mut d = 2 * dy - dx;
        let y_increment = if p0.y > p1.y { -1 } else { 1 };

        let mut y = p0.y;
        for x in p0.x..(p1.x + 1) {
            if world.is_obstacle_coords(x as usize, y as usize) {
                return true;
            }
            if d > 0 {
                y += y_increment;
                d += 2 * (dy - dx);
            } else {
                d += 2 * dy;
            }
        }
        false
    }

    /// For dy > dx
    fn path_is_blocked_high(p0: &Pos, p1: &Pos, world: &World) -> bool {
        let diff = p1 - p0;
        let dx = diff.x.abs();
        let dy = diff.y;
        let mut d = 2 * dx - dy;
        let x_increment = if p0.x > p1.x { -1 } else { 1 };

        let mut x = p0.x;
        for y in p0.y..(p1.y + 1) {
            if world.is_obstacle_coords(x as usize, y as usize) {
                return true;
            }
            if d > 0 {
                x += x_increment;
                d += 2 * (dx - dy);
            } else {
                d += 2 * dx;
            }
        }
        false
    }
}
