// Coordinate system: (0, 0) is the top-left tile and y increases downward.

export const GRID_SIZE = 12;

// Consistent visual colors for each resident ID
export const RESIDENT_COLORS = {
  ethan: '#e63946',
  gayatri: '#2a9d8f',
  aishani: '#f4a261',
  rylee: '#457b9d',
  saurya: '#9b5de5',
};

// Fallback mock residents used only when the backend is unreachable
export const residents = [
  {
    id: 'ethan',
    name: 'Ethan',
    x: 2,
    y: 3,
    color: '#e63946',
  },
  {
    id: 'gayatri',
    name: 'Gayatri',
    x: 5,
    y: 7,
    color: '#2a9d8f',
  },
  {
    id: 'aishani',
    name: 'Aishani',
    x: 8,
    y: 2,
    color: '#f4a261',
  },
  {
    id: 'rylee',
    name: 'Rylee',
    x: 10,
    y: 9,
    color: '#457b9d',
  },
  {
    id: 'saurya',
    name: 'Saurya',
    x: 6,
    y: 5,
    color: '#9b5de5',
  },
];
