#![allow(non_snake_case)]

pub mod path;
pub mod pos;
mod pos_map;
mod priority;
pub mod world;

use pyo3::prelude::*;

#[pymodule]
fn _janlukas(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    world::bind(py, m)?;
    path::bind(py, m)?;
    Ok(())
}
