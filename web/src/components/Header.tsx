import { Link, useLocation } from 'react-router-dom';

interface HeaderProps {
  className?: React.ComponentProps<'div'>['className'];
}

interface HeaderItemProps {
  route: string;
  highlite?: boolean;
  children?: React.ReactNode;
}

const routeNames = {
  '/': 'Home',
  '/workflows': 'Workflows',
};

const Header = (props: HeaderProps) => {
  const location = useLocation();

  return (
    <nav className={`w-full bg-white ${props.className}`}>
      <ul className='flex flex-row justify-center'>
        {Object.keys(routeNames).map((route, i) => (
          <HeaderItem
            key={i}
            route={route}
            highlite={location.pathname === route}>
            {routeNames[route as keyof typeof routeNames]}
          </HeaderItem>
        ))}
      </ul>
      <a
        href='/oauth2/sign_out'
        className='absolute right-0 top-0 p-4 hover:text-selected'>
        Sign out
      </a>
    </nav>
  );
};

const HeaderItem = (props: HeaderItemProps) => {
  return (
    <li>
      <Link
        to={props.route}
        className={`py-3 px-4 cursor-pointer text-lg text-black block ${
          props.highlite ? 'bg-selected' : 'hover:bg-selected'
        }`}>
        {props.children}
      </Link>
    </li>
  );
};

export default Header;
