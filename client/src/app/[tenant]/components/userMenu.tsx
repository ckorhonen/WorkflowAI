import { ArrowSwapRegular } from '@fluentui/react-icons';
import { Building, ChevronsUpDown, LogOut, LucideIcon, Settings } from 'lucide-react';
import { useState } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/Avatar/Avatar';
import { Command, CommandItem, CommandList, CommandSeparator } from '@/components/ui/Command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/Popover';
import { SimpleTooltip } from '@/components/ui/Tooltip';
import { DISABLE_AUTHENTICATION } from '@/lib/constants';
import { User } from '@/types/user';

type UserMenuCommandProps = {
  lucideIcon?: LucideIcon;
  label: string;
  icon?: React.ReactNode;
  onSelect: () => void;
  tooltip?: string;
};

function UserMenuCommand(props: UserMenuCommandProps) {
  const { lucideIcon: LucideIcon, label, icon, onSelect, tooltip } = props;

  return (
    <CommandItem onSelect={onSelect} className='cursor-pointer flex items-center gap-3 text-gray-700 font-lato'>
      <SimpleTooltip
        content={tooltip}
        asChild
        tooltipDelay={0}
        side='top'
        align='center'
        tooltipClassName='whitespace-pre-line'
      >
        <div className='flex items-center gap-2'>
          {LucideIcon && <LucideIcon size={16} strokeWidth={1.5} />}
          {icon && icon}
          <span className='text-[13px] font-normal'>{label}</span>
        </div>
      </SimpleTooltip>
    </CommandItem>
  );
}

type UserMenuProps = {
  user: User | null | undefined;
  orgState: 'selected' | 'available' | 'unavailable' | undefined;
  openUserProfile?: () => void;
  openOrganizationProfile?: () => void;
  switchOrganizations?: () => void;
  signOut?: () => void;
};

export function UserMenu(props: UserMenuProps) {
  const { user, orgState, openUserProfile, openOrganizationProfile, switchOrganizations, signOut } = props;
  const [open, setOpen] = useState(false);
  const email = user?.email;

  if (!user || DISABLE_AUTHENTICATION) return null;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger className='w-full'>
        <div className='w-full flex gap-1 pl-3 pr-2 py-2 justify-between items-center hover:bg-gray-100 border-b border-gray-200 cursor-pointer rounded-t-sm transition-colors'>
          <div className='flex flex-row items-center w-full'>
            <Avatar className='w-5 h-5 shrink-0 mr-3'>
              <AvatarImage src={user.imageUrl} />
              <AvatarFallback>{user.fullName?.[0].toUpperCase()}</AvatarFallback>
            </Avatar>
            <div className='flex flex-row items-center justify-between overflow-hidden w-full'>
              <div className='max-w-[150px] whitespace-nowrap overflow-hidden text-ellipsis font-medium text-[13px] text-gray-800'>
                {user.firstName || email}
              </div>
              <ChevronsUpDown className='h-4 w-4 shrink-0 text-gray-500' />
            </div>
          </div>
        </div>
      </PopoverTrigger>
      <PopoverContent className='w-[auto] min-w-[220px] p-1 rounded-[2px] m-1'>
        <Command>
          <CommandList>
            {orgState === 'unavailable' && openOrganizationProfile && (
              <>
                <UserMenuCommand
                  lucideIcon={Building}
                  label='Create an Organization'
                  onSelect={openOrganizationProfile}
                  tooltip={'Create an organization to start\ncollaborating with your team.'}
                />
                <CommandSeparator />
              </>
            )}

            {orgState === 'available' && (
              <>
                {openOrganizationProfile && (
                  <>
                    <UserMenuCommand
                      lucideIcon={Building}
                      label='Select an organization'
                      onSelect={openOrganizationProfile}
                      tooltip={'Join an organization to start\ncollaborating with your team.'}
                    />
                    <CommandSeparator />
                  </>
                )}
              </>
            )}

            {openUserProfile && (
              <UserMenuCommand lucideIcon={Settings} label='Manage account' onSelect={openUserProfile} />
            )}
            {orgState === 'selected' && (
              <>
                {openOrganizationProfile && (
                  <UserMenuCommand
                    lucideIcon={Building}
                    label='Organization settings'
                    onSelect={openOrganizationProfile}
                  />
                )}
                {switchOrganizations && (
                  <UserMenuCommand
                    icon={<ArrowSwapRegular className='w-4 h-4' />}
                    label='Switch Organizations'
                    onSelect={switchOrganizations}
                  />
                )}
              </>
            )}
            {signOut && <UserMenuCommand lucideIcon={LogOut} label='Sign out' onSelect={signOut} />}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
