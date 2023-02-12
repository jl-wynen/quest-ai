use crate::pos::*;
use ndarray::Array2;

pub struct PosMap<T> {
    data: Array2<T>,
    init: T,
}

impl<T> PosMap<T>
where
    T: Copy + PartialEq,
{
    pub fn new(shape: (usize, usize), init: T) -> Self {
        Self {
            data: Array2::from_elem(shape, init),
            init,
        }
    }

    pub fn get(&self, pos: &Pos) -> Option<&T> {
        self.data.get(Self::pos_to_key(pos))
    }

    pub fn get_if_set(&self, pos: &Pos) -> Option<&T> {
        self.data
            .get(Self::pos_to_key(pos))
            .and_then(|x| if x == &self.init { None } else { Some(x) })
    }

    pub fn get_or(&self, pos: &Pos, default: &T) -> T {
        *self.data.get(Self::pos_to_key(pos)).unwrap_or(default)
    }

    pub fn get_unchecked(&self, pos: &Pos) -> T {
        self.data[Self::pos_to_key(pos)]
    }

    pub fn set(&mut self, pos: &Pos, value: T) {
        self.data[Self::pos_to_key(pos)] = value;
    }

    pub fn is_set(&self, pos: &Pos) -> bool {
        self.data
            .get(Self::pos_to_key(pos))
            .map_or(false, |&x| x != self.init)
    }

    pub fn clear(&mut self) {
        self.data.fill(self.init);
    }

    fn pos_to_key(pos: &Pos) -> (usize, usize) {
        (pos.x as usize, pos.y as usize)
    }
}
